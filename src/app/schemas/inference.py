from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class InferenceEvaluateRequest(BaseModel):
    model_id: UUID
    dataset_id: UUID
    metrics: list[str] = Field(default_factory=lambda: ["accuracy", "f1", "precision", "recall"])


class InferenceBatchRequest(BaseModel):
    model_id: UUID
    dataset_id: UUID
    output_format: str = "json"


class InferenceOnlineRequest(BaseModel):
    """Matches openapi `OnlineInferenceRequest.input_data` (object | Base64 string)."""

    model_id: UUID
    input_data: dict[str, Any] | str
    checkpoint_path: str | None = None


class InferenceExportOnnxRequest(BaseModel):
    model_id: UUID
    opset_version: int = 17


class InferenceTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str = "Mock inference task created"


class InferenceResultResponse(BaseModel):
    task_id: str
    status: str
    metrics: dict[str, float] | None = None
    predictions: list[dict[str, Any]] | None = None
    download_url: str | None = None
