"""ORM models aligned with P6 DDL (`datasets` table)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DatasetRow(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(32), nullable=False, default="csv")
    file_path: Mapped[str] = mapped_column(Text, nullable=False, default="")
    num_samples: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    columns_meta: Mapped[list | dict] = mapped_column(JSON, nullable=False, default=list)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploading")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
