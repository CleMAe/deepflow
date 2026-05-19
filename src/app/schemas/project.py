"""Project schemas — aligned with openapi.yaml."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1024)
    storage_quota: int = Field(default=10240, ge=1)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1024)
    storage_quota: int | None = Field(default=None, ge=1)


class ProjectOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    owner_id: UUID
    storage_quota: int
    storage_used: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedProjects(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[ProjectOut]
