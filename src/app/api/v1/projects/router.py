"""Project CRUD API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.core.errors import AppError
from app.core.response import success
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from src.infra.db.models.project import Project

router = APIRouter(prefix="/projects", tags=["Projects"])


def _to_out(p: Project) -> ProjectOut:
    return ProjectOut(
        id=p.id,
        name=p.name,
        description=p.description,
        owner_id=p.owner_id,
        storage_quota=p.storage_quota,
        storage_used=p.storage_used,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("")
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    q = select(Project).where(Project.owner_id == user_id)
    if search:
        q = q.where(Project.name.ilike(f"%{search}%"))
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.scalars(q.order_by(Project.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return success({
        "page": page,
        "page_size": page_size,
        "total": total or 0,
        "items": [_to_out(p).model_dump(mode="json") for p in rows],
    })


@router.post("", status_code=201)
async def create_project(
    body: ProjectCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    p = Project(
        name=body.name,
        description=body.description,
        owner_id=user_id,
        storage_quota=body.storage_quota or 10240,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return success(_to_out(p).model_dump(mode="json"))


@router.get("/{project_id}")
async def get_project(
    project_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    p = db.get(Project, project_id)
    if not p or p.owner_id != user_id:
        raise AppError.not_found("Project not found")
    return success(_to_out(p).model_dump(mode="json"))


@router.put("/{project_id}")
async def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    p = db.get(Project, project_id)
    if not p or p.owner_id != user_id:
        raise AppError.not_found("Project not found")
    if body.name is not None:
        p.name = body.name
    if body.description is not None:
        p.description = body.description
    if body.storage_quota is not None:
        p.storage_quota = body.storage_quota
    db.commit()
    db.refresh(p)
    return success(_to_out(p).model_dump(mode="json"))


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    p = db.get(Project, project_id)
    if not p or p.owner_id != user_id:
        raise AppError.not_found("Project not found")
    db.delete(p)
    db.commit()
    return success({"project_id": str(project_id)})
