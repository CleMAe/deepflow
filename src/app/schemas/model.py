from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ModelCreate(BaseModel):
    name: str
    arch_type: str
    params_cfg: dict[str, Any] | None = None
    description: str | None = None


class ModelUpdate(BaseModel):
    name: str | None = None
    params_cfg: dict[str, Any] | None = None
    description: str | None = None


class ModelResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    arch_type: str
    params_cfg: dict[str, Any] | None = None
    pretrained: bool = False
    pretrained_source: str | None = None
    model_path: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ModelValidateRequest(BaseModel):
    params_cfg: dict[str, Any]


class ValidationResultSchema(BaseModel):
    valid: bool
    errors: list[dict[str, str]] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)


class PretrainedLoadRequest(BaseModel):
    source: str = "huggingface"
    repo_id: str


class LibraryModelSchema(BaseModel):
    model_id: str
    name: str
    arch_type: str
    task_type: str
    description: str
    input_shape: list[int] = Field(default_factory=list)
    num_params: int = 0
    default_hyperparams: dict[str, Any] = Field(default_factory=dict)
    supported_datasets: list[str] = Field(default_factory=list)
    pretrained_available: bool = False
