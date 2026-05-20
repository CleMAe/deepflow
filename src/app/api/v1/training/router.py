"""Training job API routes — CRUD + lifecycle control."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_storage, get_training_service, require_project_access
from app.core.response import success
from app.schemas.training import TrainingJobCreate
from app.services.training_service import TrainingService
from shared.protocols import StorageProtocol

router = APIRouter(prefix="/projects/{project_id}/training-jobs", tags=["Training"])


@router.get("")
async def list_training_jobs(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    _: UUID = Depends(require_project_access),
    svc: TrainingService = Depends(get_training_service),
    db: Session = Depends(get_db),
):
    return success(svc.list_jobs(db, project_id, page, page_size, status))


@router.post("")
async def create_training_job(
    project_id: UUID,
    body: TrainingJobCreate,
    _: UUID = Depends(require_project_access),
    svc: TrainingService = Depends(get_training_service),
    db: Session = Depends(get_db),
):
    return success(svc.create_job(db, project_id, body))


@router.get("/{job_id}")
async def get_training_job(
    project_id: UUID,
    job_id: UUID,
    _: UUID = Depends(require_project_access),
    svc: TrainingService = Depends(get_training_service),
    db: Session = Depends(get_db),
):
    return success(svc.get_job(db, project_id, job_id).model_dump(mode="json"))


@router.post("/{job_id}/start")
async def start_training_job(
    project_id: UUID,
    job_id: UUID,
    _: UUID = Depends(require_project_access),
    svc: TrainingService = Depends(get_training_service),
    db: Session = Depends(get_db),
):
    return success(svc.start_job(db, project_id, job_id).model_dump(mode="json"))


@router.post("/{job_id}/pause")
async def pause_training_job(
    project_id: UUID,
    job_id: UUID,
    _: UUID = Depends(require_project_access),
    svc: TrainingService = Depends(get_training_service),
    db: Session = Depends(get_db),
):
    return success(svc.pause_job(db, project_id, job_id).model_dump(mode="json"))


@router.post("/{job_id}/resume")
async def resume_training_job(
    project_id: UUID,
    job_id: UUID,
    _: UUID = Depends(require_project_access),
    svc: TrainingService = Depends(get_training_service),
    db: Session = Depends(get_db),
):
    return success(svc.resume_job(db, project_id, job_id).model_dump(mode="json"))


@router.post("/{job_id}/stop")
async def stop_training_job(
    project_id: UUID,
    job_id: UUID,
    _: UUID = Depends(require_project_access),
    svc: TrainingService = Depends(get_training_service),
    db: Session = Depends(get_db),
):
    return success(svc.stop_job(db, project_id, job_id).model_dump(mode="json"))


@router.get("/{job_id}/logs")
async def get_training_logs(
    project_id: UUID,
    job_id: UUID,
    tail: int = Query(200, ge=1),
    _: UUID = Depends(require_project_access),
    svc: TrainingService = Depends(get_training_service),
    db: Session = Depends(get_db),
):
    return success(svc.get_logs(db, project_id, job_id, tail).model_dump(mode="json"))


@router.get("/{job_id}/checkpoints")
async def list_checkpoints(
    project_id: UUID,
    job_id: UUID,
    _: UUID = Depends(require_project_access),
    svc: TrainingService = Depends(get_training_service),
    db: Session = Depends(get_db),
):
    ckpts = svc.get_checkpoints(db, project_id, job_id)
    return success({"checkpoints": [c.model_dump(mode="json") for c in ckpts]})
