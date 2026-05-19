"""Project routes — /api/v1/projects/* (P6 contract)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.response import success
from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


def _project_service(db: Session = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


@router.get("", summary="List projects")
def list_projects(
    current_user: Annotated[UUID, Depends(get_current_user)],
    svc: ProjectService = Depends(_project_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
) -> dict:
    data = svc.list_projects(current_user, page=page, page_size=page_size, search=search)
    return success(data.model_dump(mode="json"))


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new project")
def create_project(
    body: ProjectCreate,
    current_user: Annotated[UUID, Depends(get_current_user)],
    svc: ProjectService = Depends(_project_service),
) -> dict:
    project = svc.create_project(current_user, body)
    return success(project.model_dump(mode="json"))


@router.get("/{project_id}", summary="Get project detail")
def get_project(
    project_id: UUID,
    current_user: Annotated[UUID, Depends(get_current_user)],
    svc: ProjectService = Depends(_project_service),
) -> dict:
    project = svc.get_project(project_id, current_user)
    return success(project.model_dump(mode="json"))


@router.put("/{project_id}", summary="Update project")
def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    current_user: Annotated[UUID, Depends(get_current_user)],
    svc: ProjectService = Depends(_project_service),
) -> dict:
    project = svc.update_project(project_id, current_user, body)
    return success(project.model_dump(mode="json"))


@router.delete("/{project_id}", summary="Delete project")
def delete_project(
    project_id: UUID,
    current_user: Annotated[UUID, Depends(get_current_user)],
    svc: ProjectService = Depends(_project_service),
) -> dict:
    svc.delete_project(project_id, current_user)
    return success(None)
