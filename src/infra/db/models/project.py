"""Project model — top-level organization unit."""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.db.base import Base, TimestampUpdateMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.infra.db.models.agent import Agent
    from src.infra.db.models.dataset import Dataset
    from src.infra.db.models.experiment import Experiment
    from src.infra.db.models.ml_model import MLModel
    from src.infra.db.models.training_job import TrainingJob
    from src.infra.db.models.user import User


class Project(UUIDPrimaryKeyMixin, TimestampUpdateMixin, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    storage_quota: Mapped[int] = mapped_column(Integer, nullable=False, default=10240)
    storage_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    owner: Mapped["User"] = relationship(back_populates="projects")
    datasets: Mapped[List["Dataset"]] = relationship(back_populates="project")
    models: Mapped[List["MLModel"]] = relationship(back_populates="project")
    training_jobs: Mapped[List["TrainingJob"]] = relationship(back_populates="project")
    agents: Mapped[List["Agent"]] = relationship(back_populates="project")
    experiments: Mapped[List["Experiment"]] = relationship(back_populates="project")
