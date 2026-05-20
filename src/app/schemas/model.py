"""Pydantic schemas for Model Library and Project Models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# --- Library models (read-only registry) ---

class LibraryModel(BaseModel):
    model_id: str
    name: str
    arch_type: str
    task_type: str
    description: str | None = None
    input_shape: list[int] = Field(default_factory=list)
    num_params: int | None = None
    default_hyperparams: dict[str, Any] = Field(default_factory=dict)
    supported_datasets: list[str] = Field(default_factory=list)
    pretrained_available: bool = False


# --- Project model CRUD ---

class ModelCreate(BaseModel):
    name: str
    arch_type: str
    params_cfg: dict[str, Any] | None = None
    description: str | None = None


class ModelUpdate(BaseModel):
    name: str | None = None
    params_cfg: dict[str, Any] | None = None
    description: str | None = None


class ModelOut(BaseModel):
    id: str
    project_id: str
    name: str
    arch_type: str
    params_cfg: dict[str, Any] | None = None
    pretrained: bool = False
    pretrained_source: str | None = None
    model_path: str | None = None
    description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ModelValidateRequest(BaseModel):
    params_cfg: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    valid: bool
    errors: list[dict[str, str]] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)


class PretrainedLoadRequest(BaseModel):
    source: str = "huggingface"
    repo_id: str | None = None


class PretrainedLoadStatus(BaseModel):
    status: str
    model_path: str | None = None
