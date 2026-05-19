"""Dataset model — uploaded / cleaned data metadata."""

from typing import TYPE_CHECKING, List, Optional

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.db.base import Base, TimestampUpdateMixin, UUIDPrimaryKeyMixin
from src.infra.db.types import JSONType

if TYPE_CHECKING:
    from src.infra.db.models.project import Project
    from src.infra.db.models.training_job import TrainingJob


class DatasetFormat(str, enum.Enum):
    CSV = "csv"
    JSON = "json"
    IMAGE = "image"
    OTHER = "other"


class DatasetStatus(str, enum.Enum):
    UPLOADING = "uploading"
    READY = "ready"
    CLEANING = "cleaning"
    CLEANED = "cleaned"
    ERROR = "error"


class Dataset(UUIDPrimaryKeyMixin, TimestampUpdateMixin, Base):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    project_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    format: Mapped[DatasetFormat] = mapped_column(
        Enum(DatasetFormat, name="dataset_format", native_enum=False),
        nullable=False,
        default=DatasetFormat.OTHER,
    )
    file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    num_samples: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    num_columns: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    columns_meta: Mapped[Optional[list]] = mapped_column(JSONType, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSONType, nullable=True)
    status: Mapped[DatasetStatus] = mapped_column(
        Enum(DatasetStatus, name="dataset_status", native_enum=False),
        nullable=False,
        default=DatasetStatus.UPLOADING,
    )
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="datasets")
    training_jobs: Mapped[List["TrainingJob"]] = relationship(
        back_populates="dataset",
        foreign_keys="TrainingJob.dataset_id",
    )
