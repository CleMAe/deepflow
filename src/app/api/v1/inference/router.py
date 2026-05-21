from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_project_access, get_db, get_inference_service
from app.core.response import success
from app.schemas.inference import (
    InferenceBatchRequest,
    InferenceEvaluateRequest,
    InferenceExportOnnxRequest,
    InferenceOnlineRequest,
)
from app.services.inference_service import InferenceService  # noqa: F401 — type annotation

router = APIRouter(prefix="/projects/{project_id}/inference", tags=["Inference"])


@router.post("/evaluate")
async def evaluate(
    project_id: UUID,
    body: InferenceEvaluateRequest,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
    svc: InferenceService = Depends(get_inference_service),
):
    result = svc.evaluate(
        db=db,
        project_id=project_id,
        model_id=body.model_id,
        dataset_id=body.dataset_id,
        checkpoint_path=body.checkpoint_path,
        metrics=body.metrics,
    )
    return success(result.model_dump())


@router.post("/batch")
async def batch_inference(
    project_id: UUID,
    body: InferenceBatchRequest,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
    svc: InferenceService = Depends(get_inference_service),
):
    result = svc.start_batch_inference(
        db=db,
        project_id=project_id,
        model_id=body.model_id,
        dataset_id=body.dataset_id,
        checkpoint_path=body.checkpoint_path,
        output_format=body.output_format,
    )
    return success(result.model_dump())


@router.get("/{task_id}")
async def get_inference_result(
    project_id: UUID,
    task_id: str,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
    svc: InferenceService = Depends(get_inference_service),
):
    result = svc.get_inference_result(db=db, project_id=project_id, task_id=task_id)
    return success(result.model_dump())


@router.post("/online")
async def online_inference(
    project_id: UUID,
    body: InferenceOnlineRequest,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
    svc: InferenceService = Depends(get_inference_service),
):
    result = svc.online_inference(
        db=db,
        project_id=project_id,
        model_id=body.model_id,
        input_data=body.input_data,
        checkpoint_path=body.checkpoint_path,
    )
    return success(result.model_dump())


@router.post("/export-onnx")
async def export_onnx(
    project_id: UUID,
    body: InferenceExportOnnxRequest,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
    svc: InferenceService = Depends(get_inference_service),
):
    result = svc.export_onnx(
        db=db,
        project_id=project_id,
        model_id=body.model_id,
        checkpoint_path=body.checkpoint_path,
        opset_version=body.opset_version,
        dynamic_batch=body.dynamic_batch,
    )
    return success(result.model_dump())
