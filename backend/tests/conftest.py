"""
Pytest fixtures — SQLite in-memory DB with per-test transaction rollback.

Integration with FastAPI TestClient is prepared; wire `app` once P6 lands the skeleton.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from tests.factories.base import TestRecordFactory
from tests.support.models import Base

# P6: from app.main import app
# P6: from app.database import get_db


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    """Shared in-memory SQLite engine (StaticPool keeps a single connection)."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    """
    Yield a Session inside a SAVEPOINT; roll back after each test for isolation.
    """
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

    try:
        yield session
    finally:
        TestRecordFactory._meta.sqlalchemy_session = None  # noqa: SLF001
        session.close()
        outer.rollback()
        connection.close()


@pytest.fixture
def factories(db_session: Session) -> type[TestRecordFactory]:
    """Expose the primary factory; add module-specific factories here later."""
    return TestRecordFactory


@pytest.fixture
def api_client():
    """
    FastAPI TestClient — enable when `backend.app.main:app` exists.

    Example (P6):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as client:
            yield client
        app.dependency_overrides.clear()
    """
    return None  # FastAPI app not wired yet — enable when P6 skeleton lands
