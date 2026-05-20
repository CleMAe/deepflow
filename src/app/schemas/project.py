"""Pydantic schemas for Project endpoints — matches openapi.yaml."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1024)
    storage_quota: int | None = Field(default=None, description="Storage quota in MB")


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1024)
    storage_quota: int | None = Field(default=None, ge=0)


class ProjectOut(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    owner_id: UUID
    storage_quota: int
    storage_used: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
