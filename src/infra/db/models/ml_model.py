"""ML model configuration — per-project model definitions."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.db.base import Base, TimestampUpdateMixin, UUIDPrimaryKeyMixin
from src.infra.db.types import JSONType

if TYPE_CHECKING:
    from src.infra.db.models.project import Project
    from src.infra.db.models.training_job import TrainingJob


class MLModel(UUIDPrimaryKeyMixin, TimestampUpdateMixin, Base):
    __tablename__ = "models"

    project_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    arch_type: Mapped[str] = mapped_column(String(64), nullable=False)
    params_cfg: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    pretrained: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pretrained_source: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    model_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="models")
    training_jobs: Mapped[List["TrainingJob"]] = relationship(back_populates="model")
