"""Model library + project model configuration API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_project_access
from app.core.errors import AppError
from app.core.response import success
from app.schemas.model import (
    LibraryModel,
    ModelCreate,
    ModelOut,
    ModelUpdate,
    ModelValidateRequest,
    PretrainedLoadRequest,
    PretrainedLoadStatus,
)
from app.services.model_library import ModelLibraryService
from src.infra.db.models.ml_model import MLModel

library_svc = ModelLibraryService()

# --- Library (global, read-only) ---

library_router = APIRouter(tags=["ModelLibrary"])


@library_router.get("/models/library")
async def list_model_library(
    task_type: str | None = None,
    search: str | None = None,
):
    items = library_svc.list_models(task_type, search)
    return success([LibraryModel(**m).model_dump(mode="json") for m in items])


@library_router.get("/models/library/{model_id}")
async def get_model_library_detail(model_id: str):
    item = library_svc.get_model(model_id)
    if not item:
        raise AppError.not_found("Model not found in library")
    return success(LibraryModel(**item).model_dump(mode="json"))


# --- Project models (CRUD) ---

router = APIRouter(prefix="/projects/{project_id}/models", tags=["Models"])


def _model_to_out(m: MLModel) -> ModelOut:
    return ModelOut(
        id=str(m.id),
        project_id=str(m.project_id),
        name=m.name,
        arch_type=m.arch_type,
        params_cfg=m.params_cfg,
        pretrained=m.pretrained,
        pretrained_source=m.pretrained_source,
        model_path=m.model_path,
        description=m.description,
        created_at=m.created_at.isoformat() if m.created_at else None,
        updated_at=m.updated_at.isoformat() if m.updated_at else None,
    )


@router.get("")
async def list_project_models(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
):
    q = (
        select(MLModel)
        .where(MLModel.project_id == project_id)
        .order_by(MLModel.created_at.desc())
    )
    all_rows = db.scalars(select(MLModel).where(MLModel.project_id == project_id)).all()
    total = len(all_rows)
    offset = (page - 1) * page_size
    rows = db.scalars(q.offset(offset).limit(page_size)).all()
    return success({
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": [_model_to_out(m).model_dump(mode="json") for m in rows],
    })


@router.post("")
async def create_project_model(
    project_id: UUID,
    body: ModelCreate,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
):
    m = MLModel(
        project_id=project_id,
        name=body.name,
        arch_type=body.arch_type,
        params_cfg=body.params_cfg,
        description=body.description,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return success(_model_to_out(m).model_dump(mode="json"))


@router.get("/{m_id}")
async def get_project_model(
    project_id: UUID,
    m_id: UUID,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
):
    m = db.get(MLModel, m_id)
    if not m or m.project_id != project_id:
        raise AppError.not_found("Model not found")
    return success(_model_to_out(m).model_dump(mode="json"))


@router.put("/{m_id}")
async def update_project_model(
    project_id: UUID,
    m_id: UUID,
    body: ModelUpdate,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
):
    m = db.get(MLModel, m_id)
    if not m or m.project_id != project_id:
        raise AppError.not_found("Model not found")
    if body.name is not None:
        m.name = body.name
    if body.params_cfg is not None:
        m.params_cfg = body.params_cfg
    if body.description is not None:
        m.description = body.description
    db.commit()
    db.refresh(m)
    return success(_model_to_out(m).model_dump(mode="json"))


@router.delete("/{m_id}")
async def delete_project_model(
    project_id: UUID,
    m_id: UUID,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
):
    m = db.get(MLModel, m_id)
    if not m or m.project_id != project_id:
        raise AppError.not_found("Model not found")
    db.delete(m)
    db.commit()
    return success({"model_id": str(m_id)})


@router.post("/{m_id}/validate")
async def validate_model_config(
    project_id: UUID,
    m_id: UUID,
    body: ModelValidateRequest,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
):
    m = db.get(MLModel, m_id)
    if not m or m.project_id != project_id:
        raise AppError.not_found("Model not found")
    result = library_svc.validate_config(m.arch_type, body.params_cfg)
    return success(result.__dict__)


@router.post("/{m_id}/pretrained")
async def load_pretrained_weights(
    project_id: UUID,
    m_id: UUID,
    body: PretrainedLoadRequest,
    _: UUID = Depends(require_project_access),
    db: Session = Depends(get_db),
):
    m = db.get(MLModel, m_id)
    if not m or m.project_id != project_id:
        raise AppError.not_found("Model not found")
    m.pretrained = True
    m.pretrained_source = body.source
    m.model_path = f"/projects/{project_id}/models/{m_id}/checkpoint/pretrained.pth"
    db.commit()
    db.refresh(m)
    return success(PretrainedLoadStatus(status="ready", model_path=m.model_path).model_dump(mode="json"))
