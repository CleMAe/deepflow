"""
Pytest fixtures — SQLite in-memory DB with per-test transaction rollback.

Wires FastAPI TestClient with dependency overrides for integration tests.
"""

# ruff: noqa: E402 — sys.path must be configured before app/tests imports

from __future__ import annotations

import sys
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
for _path in (_ROOT, _SRC):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import src.infra.db.models  # noqa: F401 — register ORM metadata with Base
from src.infra.db.base import Base
from tests.factories.dataset import DatasetFactory
from tests.factories.project import ProjectFactory
from tests.factories.user import UserFactory

_TEST_DATABASE_URL = "sqlite://"


@asynccontextmanager
async def _noop_lifespan(_app: Any) -> AsyncIterator[None]:
    """Bypass app startup: test engine already owns DDL; avoid closing db_session."""
    yield


def _swap_lifespan_context(app: Any) -> Any | None:
    """Replace router lifespan with no-op; return original for teardown."""
    router = app.router
    original = getattr(router, "lifespan_context", None)
    if original is not None:
        router.lifespan_context = _noop_lifespan
    return original


def _is_sqlite_url(database_url: str) -> bool:
    return database_url.strip().lower().startswith("sqlite")


def create_test_engine(database_url: str | None = None) -> Engine:
    """Create engine for tests; SQLite gets thread-safe in-memory pool settings."""
    url = database_url or _TEST_DATABASE_URL
    if _is_sqlite_url(url):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    return create_engine(url, echo=False)


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Isolate process env per test; avoids module-level os.environ side effects."""
    monkeypatch.setenv("DATABASE_URL", _TEST_DATABASE_URL)
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("DEV_ALLOW_ANONYMOUS", "false")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-32chars-minimum")

    from src.infra.config import get_settings

    get_settings.cache_clear()

    from app.core import config

    config.settings = config.Settings()


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    """Shared in-memory SQLite engine; schema matches src.infra.db.base.Base only."""
    eng = create_test_engine(_TEST_DATABASE_URL)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    """Yield a Session inside a SAVEPOINT; roll back after each test for isolation."""
    connection = engine.connect()
    outer = connection.begin()
    session = sessionmaker(bind=connection, expire_on_commit=False)()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess: Session, trans: Any) -> None:
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    UserFactory._meta.sqlalchemy_session = session  # noqa: SLF001
    ProjectFactory._meta.sqlalchemy_session = session  # noqa: SLF001
    DatasetFactory._meta.sqlalchemy_session = session  # noqa: SLF001

    try:
        yield session
    finally:
        UserFactory._meta.sqlalchemy_session = None  # noqa: SLF001
        ProjectFactory._meta.sqlalchemy_session = None  # noqa: SLF001
        DatasetFactory._meta.sqlalchemy_session = None  # noqa: SLF001
        session.close()
        outer.rollback()
        connection.close()


@pytest.fixture
def user_factory(db_session: Session) -> type[UserFactory]:
    return UserFactory


@pytest.fixture
def project_factory(db_session: Session) -> type[ProjectFactory]:
    return ProjectFactory


@pytest.fixture
def dataset_factory(db_session: Session) -> type[DatasetFactory]:
    return DatasetFactory


@pytest.fixture
def api_client(db_session: Session, _test_env: None) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with test DB session injected via dependency_overrides."""
    from app.db.session import get_db
    from app.main import app

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    original_lifespan = _swap_lifespan_context(app)
    # Fallback for routers without lifespan_context (legacy Starlette startup hooks)
    with (
        patch("app.main.init_db"),
        patch("app.main.seed_demo_datasets"),
    ):
        try:
            with TestClient(app) as client:
                yield client
        finally:
            if original_lifespan is not None:
                app.router.lifespan_context = original_lifespan
            app.dependency_overrides.clear()
