"""Smoke tests validating pytest + factory_boy + SQLite fixtures."""

from __future__ import annotations

from sqlalchemy import select

from tests.factories.base import TestRecordFactory
from tests.support.models import TestRecord


def test_sqlite_session_isolated(db_session, factories):
    record = factories.create(name="alpha")
    assert record.id
    assert record.name == "alpha"

    rows = db_session.scalars(select(TestRecord)).all()
    assert len(rows) == 1


def test_transaction_rollback_between_tests(db_session):
    """Previous test data must not leak (verified by empty table)."""
    rows = db_session.scalars(select(TestRecord)).all()
    assert rows == []


def test_factory_boy_batch(db_session):
    batch = TestRecordFactory.create_batch(3)
    assert len(batch) == 3
    assert len(db_session.scalars(select(TestRecord)).all()) == 3
