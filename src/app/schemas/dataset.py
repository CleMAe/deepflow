"""Pydantic models aligned with `docs/api/openapi.yaml` Dataset schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

DatasetFormat = Literal["csv", "json", "image", "other"]
DatasetStatus = Literal["uploading", "ready", "cleaning", "cleaned", "error"]


class ColumnMetaSchema(BaseModel):
    name: str
    dtype: str
    nullable: bool = True
    unique_count: int | None = None
    sample_values: list[Any] = Field(default_factory=list)


class DatasetCreate(BaseModel):
    name: str
    format: DatasetFormat = "csv"
    description: str | None = None
    tags: list[str] = Field(default_factory=list)


class DatasetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None


class DatasetSchema(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    format: DatasetFormat
    file_path: str
    num_samples: int = 0
    num_columns: int = 0
    columns_meta: list[ColumnMetaSchema] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    status: DatasetStatus
    size_bytes: int | None = None
    created_at: datetime
    updated_at: datetime | None = None


class PaginatedDatasets(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[DatasetSchema]


class UploadInitRequest(BaseModel):
    filename: str
    total_size: int
    total_chunks: int
    dataset_name: str | None = None
    format: DatasetFormat | None = None


class UploadSessionSchema(BaseModel):
    upload_id: UUID
    chunk_size: int
    received_chunks: list[int] = Field(default_factory=list)


class UploadCompleteRequest(BaseModel):
    total_chunks: int
    dataset_name: str | None = None
    tags: list[str] = Field(default_factory=list)


class DatasetPreviewSchema(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    limit: int = 100


class ImageItemSchema(BaseModel):
    id: UUID
    filename: str
    thumbnail_path: str
    labels: list[str] = Field(default_factory=list)
    width: int
    height: int


class PaginatedImages(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[ImageItemSchema]


class BatchLabelUpdate(BaseModel):
    items: list[dict[str, Any]]  # validated in service: image_id + labels
