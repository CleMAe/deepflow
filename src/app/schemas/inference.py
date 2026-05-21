from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class InferenceEvaluateRequest(BaseModel):
    model_id: UUID
    dataset_id: UUID
    checkpoint_path: str | None = None
    metrics: list[str] = Field(default_factory=lambda: ["accuracy", "f1", "precision", "recall"])


class InferenceBatchRequest(BaseModel):
    model_id: UUID
    dataset_id: UUID
    checkpoint_path: str | None = None
    output_format: str = "json"


class InferenceOnlineRequest(BaseModel):
    model_id: UUID
    input_data: dict[str, Any] | str
    checkpoint_path: str | None = None


class InferenceExportOnnxRequest(BaseModel):
    model_id: UUID
    checkpoint_path: str | None = None
    opset_version: int = 17
    dynamic_batch: bool = True


class OnlineInferenceResult(BaseModel):
    prediction: Any
    confidence: float | None = None
    probabilities: dict[str, float] | None = None
    latency_ms: float | None = None


class PredictionItem(BaseModel):
    input: Any = None
    prediction: Any = None
    confidence: float | None = None


class InferenceTaskResponse(BaseModel):
    task_id: str
    model_id: str | None = None
    dataset_id: str | None = None
    status: str
    progress: float | None = None
    result_path: str | None = None
    predictions: list[PredictionItem] | None = None
    created_at: str | None = None
    finished_at: str | None = None


class EvaluateResult(BaseModel):
    model_id: str
    dataset_id: str
    metrics: dict[str, float] = Field(default_factory=dict)
    confusion_matrix: list[list[int]] | None = None
    classification_report: dict[str, Any] | None = None
    num_samples: int = 0


class ExportOnnxResult(BaseModel):
    task_id: str
    status: str
    onnx_path: str | None = None
    opset_version: int = 17
