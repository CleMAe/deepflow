"""Experiment model — training run records & comparison."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.infra.db.types import JSONType

if TYPE_CHECKING:
    from src.infra.db.models.project import Project
    from src.infra.db.models.training_job import TrainingJob


class Experiment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "experiments"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("training_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    metrics: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    params_snap: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSONType, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="experiments")
    job: Mapped["TrainingJob"] = relationship(back_populates="experiments")
