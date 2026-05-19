"""
Pytest fixtures — SQLite in-memory DB with per-test transaction rollback.

Wires FastAPI TestClient with dependency overrides for integration tests.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any

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

# Must set before app imports read Settings
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("DEV_ALLOW_ANONYMOUS", "false")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-32chars-minimum")

from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from src.infra.db.base import Base as InfraBase  # noqa: E402
import src.infra.db.models  # noqa: F401, E402 — register ORM metadata

from tests.factories.base import TestRecordFactory
from tests.factories.dataset import DatasetFactory
from tests.factories.project import ProjectFactory
from tests.factories.user import UserFactory
from tests.support.models import Base as TestBase

AUTH_PREFIX = "/api/v1/auth"


def _is_sqlite_url(database_url: str) -> bool:
    return database_url.strip().lower().startswith("sqlite")


def create_test_engine(database_url: str | None = None) -> Engine:
    """Create engine for tests; SQLite gets thread-safe in-memory pool settings."""
    url = database_url or os.environ.get("DATABASE_URL", "sqlite://")
    if _is_sqlite_url(url):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    return create_engine(url, echo=False)


def _bind_infra_engine(engine: Engine) -> None:
    """Point infra session factory at the test engine (same thread/pool rules)."""
    from src.infra.db import session as infra_session

    infra_session._engine = engine
    infra_session.SessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    """Shared test engine; SQLite uses StaticPool + check_same_thread=False."""
    database_url = os.environ.get("DATABASE_URL", "sqlite://")
    eng = create_test_engine(database_url)
    _bind_infra_engine(eng)
    TestBase.metadata.create_all(eng)
    InfraBase.metadata.create_all(eng)
    yield eng
    TestBase.metadata.drop_all(eng)
    InfraBase.metadata.drop_all(eng)
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

    TestRecordFactory._meta.sqlalchemy_session = session  # noqa: SLF001
    UserFactory._meta.sqlalchemy_session = session  # noqa: SLF001
    ProjectFactory._meta.sqlalchemy_session = session  # noqa: SLF001
    DatasetFactory._meta.sqlalchemy_session = session  # noqa: SLF001

    try:
        yield session
    finally:
        TestRecordFactory._meta.sqlalchemy_session = None  # noqa: SLF001
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
def factories(db_session: Session) -> type[TestRecordFactory]:
    return TestRecordFactory


@pytest.fixture
def api_client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with in-memory DB session override."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
