"""Experiment API routes — tracking & comparison."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_project_access
from app.core.response import success
from app.schemas.experiment import CompareExperimentsRequest
from app.services.experiment_service import ExperimentService

router = APIRouter(prefix="/projects/{project_id}/experiments", tags=["Experiments"])

_svc = ExperimentService()


@router.get("")
async def list_experiments(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
):
    return success(_svc.list_experiments(db, project_id, page, page_size))


@router.get("/{exp_id}")
async def get_experiment(
    project_id: UUID,
    exp_id: UUID,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
):
    return success(_svc.get_experiment(db, project_id, exp_id).model_dump(mode="json"))


@router.put("/{exp_id}")
async def update_experiment(
    project_id: UUID,
    exp_id: UUID,
    body: dict,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
):
    from app.schemas.experiment import ExperimentUpdate
    payload = ExperimentUpdate(**body)
    return success(_svc.update_experiment(db, project_id, exp_id, payload).model_dump(mode="json"))


@router.post("/compare")
async def compare_experiments(
    project_id: UUID,
    body: CompareExperimentsRequest,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
):
    result = _svc.compare_experiments(db, project_id, body.experiment_ids)
    return success(result.model_dump(mode="json"))
