"""Pydantic schemas for Experiments."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExperimentOut(BaseModel):
    id: str
    project_id: str
    job_id: str
    name: str | None = None
    metrics: dict[str, Any] | None = None
    params_snap: dict[str, Any] | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    created_at: str | None = None


class ExperimentUpdate(BaseModel):
    tags: list[str] | None = None
    notes: str | None = None


class CompareExperimentsRequest(BaseModel):
    experiment_ids: list[str] = Field(..., min_length=2)


class ExperimentComparison(BaseModel):
    experiments: list[ExperimentOut] = Field(default_factory=list)
    metric_comparison: dict[str, list[float | None]] = Field(default_factory=dict)
