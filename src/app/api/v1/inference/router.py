from uuid import UUID, uuid4

from fastapi import APIRouter, Depends

from app.api.deps import require_project_access
from app.core.response import success
from app.schemas.inference import (
    InferenceBatchRequest,
    InferenceEvaluateRequest,
    InferenceExportOnnxRequest,
    InferenceOnlineRequest,
)

router = APIRouter(prefix="/projects/{project_id}/inference", tags=["Inference"])


@router.post("/evaluate")
async def evaluate(
    project_id: UUID,
    body: InferenceEvaluateRequest,
    _: UUID = Depends(require_project_access),
):
    return success({"task_id": str(uuid4()), "status": "completed", "message": "Mock evaluation"})


@router.post("/batch")
async def batch_inference(
    project_id: UUID,
    body: InferenceBatchRequest,
    _: UUID = Depends(require_project_access),
):
    return success({"task_id": str(uuid4()), "status": "completed"})


@router.get("/{task_id}")
async def get_inference_result(
    project_id: UUID,
    task_id: str,
    _: UUID = Depends(require_project_access),
):
    return success(
        {
            "task_id": task_id,
            "status": "completed",
            "metrics": {"accuracy": 0.92, "f1": 0.91},
            "predictions": [],
            "download_url": f"/mock/inference/{task_id}/results.json",
        }
    )


@router.post("/online")
async def online_inference(
    project_id: UUID,
    body: InferenceOnlineRequest,
    _: UUID = Depends(require_project_access),
):
    return success(
        {
            "prediction": {"label": "mock", "confidence": 0.97},
            "model_id": str(body.model_id),
            "input_data": body.input_data,
        }
    )


@router.post("/export-onnx")
async def export_onnx(
    project_id: UUID,
    body: InferenceExportOnnxRequest,
    _: UUID = Depends(require_project_access),
):
    return success(
        {
            "task_id": str(uuid4()),
            "status": "completed",
            "onnx_path": f"/mock/models/{body.model_id}/model.onnx",
            "opset_version": body.opset_version,
        }
    )
