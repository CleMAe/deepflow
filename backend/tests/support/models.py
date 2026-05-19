"""
Temporary SQLAlchemy models for pytest / factory_boy scaffolding.

P6: replace imports in conftest with real `app.models` once Alembic migrations land.
"""

from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TestRecord(Base):
    """Minimal table to validate DB fixtures before production models exist."""

    __tablename__ = "test_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
