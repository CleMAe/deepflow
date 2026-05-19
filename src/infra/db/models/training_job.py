"""Training job model — training task lifecycle & metrics."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

import enum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.db.base import Base, TimestampUpdateMixin, UUIDPrimaryKeyMixin
from src.infra.db.types import JSONType

if TYPE_CHECKING:
    from src.infra.db.models.dataset import Dataset
    from src.infra.db.models.experiment import Experiment
    from src.infra.db.models.ml_model import MLModel
    from src.infra.db.models.project import Project


class TrainingJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingJob(UUIDPrimaryKeyMixin, TimestampUpdateMixin, Base):
    __tablename__ = "training_jobs"

    project_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    model_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("models.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    dataset_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("datasets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    val_dataset_id: Mapped[Optional[str]] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
    )
    hyperparams: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    status: Mapped[TrainingJobStatus] = mapped_column(
        Enum(TrainingJobStatus, name="training_job_status", native_enum=False),
        nullable=False,
        default=TrainingJobStatus.PENDING,
        index=True,
    )
    device: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, default="auto")
    current_epoch: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_epochs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metrics: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    checkpoint: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="training_jobs")
    model: Mapped["MLModel"] = relationship(back_populates="training_jobs")
    dataset: Mapped["Dataset"] = relationship(
        back_populates="training_jobs",
        foreign_keys=[dataset_id],
    )
    experiments: Mapped[List["Experiment"]] = relationship(back_populates="job")
