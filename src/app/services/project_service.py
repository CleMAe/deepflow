"""Project CRUD service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ERR_PROJECT_FORBIDDEN, ERR_PROJECT_NOT_FOUND, AppError
from app.schemas.project import PaginatedProjects, ProjectCreate, ProjectOut, ProjectUpdate
from src.infra.db.models.project import Project


class ProjectService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def _get_owned(self, project_id: UUID, owner_id: UUID) -> Project:
        project = self._db.get(Project, project_id)
        if project is None:
            raise AppError.not_found("Project not found", code=ERR_PROJECT_NOT_FOUND)
        if project.owner_id != owner_id:
            raise AppError.forbidden("No access to this project", code=ERR_PROJECT_FORBIDDEN)
        return project

    def list_projects(
        self,
        owner_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> PaginatedProjects:
        safe_page = max(1, page)
        safe_size = min(max(1, page_size), 100)
        stmt = select(Project).where(Project.owner_id == owner_id)
        if search:
            stmt = stmt.where(Project.name.ilike(f"%{search}%"))
        count_stmt = select(func.count()).select_from(Project).where(Project.owner_id == owner_id)
        if search:
            count_stmt = count_stmt.where(Project.name.ilike(f"%{search}%"))
        total = self._db.scalar(count_stmt) or 0
        rows = self._db.scalars(
            stmt.order_by(Project.created_at.desc())
            .offset((safe_page - 1) * safe_size)
            .limit(safe_size)
        ).all()
        return PaginatedProjects(
            page=safe_page,
            page_size=safe_size,
            total=int(total),
            items=[ProjectOut.model_validate(row) for row in rows],
        )

    def create_project(self, owner_id: UUID, body: ProjectCreate) -> ProjectOut:
        project = Project(
            name=body.name,
            description=body.description,
            owner_id=owner_id,
            storage_quota=body.storage_quota,
            storage_used=0,
        )
        self._db.add(project)
        self._db.flush()
        self._db.refresh(project)
        return ProjectOut.model_validate(project)

    def get_project(self, project_id: UUID, owner_id: UUID) -> ProjectOut:
        return ProjectOut.model_validate(self._get_owned(project_id, owner_id))

    def update_project(
        self, project_id: UUID, owner_id: UUID, body: ProjectUpdate
    ) -> ProjectOut:
        project = self._get_owned(project_id, owner_id)
        if body.name is not None:
            project.name = body.name
        if body.description is not None:
            project.description = body.description
        if body.storage_quota is not None:
            project.storage_quota = body.storage_quota
        self._db.flush()
        self._db.refresh(project)
        return ProjectOut.model_validate(project)

    def delete_project(self, project_id: UUID, owner_id: UUID) -> None:
        project = self._get_owned(project_id, owner_id)
        self._db.delete(project)
        self._db.flush()
