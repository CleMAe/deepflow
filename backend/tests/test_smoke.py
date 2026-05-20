"""Smoke tests validating pytest + factory_boy + SQLite fixtures."""

from __future__ import annotations

from sqlalchemy import select

from src.infra.db.models.user import User
from tests.factories.user import UserFactory


def test_sqlite_session_isolated(db_session, user_factory):
    user = user_factory(username="alpha_user")
    assert user.id
    assert user.username == "alpha_user"

    rows = db_session.scalars(select(User)).all()
    assert len(rows) == 1


def test_transaction_rollback_between_tests(db_session):
    """Previous test data must not leak (verified by empty table)."""
    rows = db_session.scalars(select(User)).all()
    assert rows == []


def test_factory_boy_batch(db_session):
    batch = UserFactory.create_batch(3)
    assert len(batch) == 3
    assert len(db_session.scalars(select(User)).all()) == 3
