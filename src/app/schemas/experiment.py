from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ExperimentResponse(BaseModel):
    id: UUID
    project_id: UUID
    job_id: UUID
    name: str | None = None
    metrics: dict[str, Any] | None = None
    params_snap: dict[str, Any] | None = None
    tags: list[str] | None = None
    notes: str | None = None
    created_at: datetime | None = None


class ExperimentUpdate(BaseModel):
    tags: list[str] | None = None
    notes: str | None = None


class CompareExperimentsRequest(BaseModel):
    experiment_ids: list[UUID] = Field(..., min_length=2)


class ExperimentComparisonSchema(BaseModel):
    experiments: list[ExperimentResponse]
    metric_comparison: dict[str, list[float]] = Field(default_factory=dict)
    param_diff: dict[str, Any] = Field(default_factory=dict)
