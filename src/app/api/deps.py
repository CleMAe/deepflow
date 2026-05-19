"""FastAPI dependencies — Protocol implementations injected here (swap at integration)."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ERR_AUTH_INVALID, ERR_PROJECT_FORBIDDEN, ERR_PROJECT_NOT_FOUND, AppError
from app.core.security import decode_token
from app.db.session import get_db
from app.repositories.dataset_repository import DatasetRepository
from app.services.cleaning_mock import MockCleaningService
from app.services.dataset_service import DatasetService
from app.services.storage_mock import MockFileStorage
from app.services.upload_service import UploadService
from shared.protocols import StorageProtocol
from src.infra.db.models.project import Project

_bearer = HTTPBearer(auto_error=False)


@lru_cache
def get_storage() -> StorageProtocol:
    """Replace with P6 `RealFileStorage` at Day3 integration."""
    return MockFileStorage()


def get_dataset_repo(db: Session = Depends(get_db)) -> DatasetRepository:
    return DatasetRepository(db)


def get_dataset_service(
    repo: DatasetRepository = Depends(get_dataset_repo),
    storage: StorageProtocol = Depends(get_storage),
) -> DatasetService:
    return DatasetService(repo, storage)


def get_upload_service(
    storage: StorageProtocol = Depends(get_storage),
    repo: DatasetRepository = Depends(get_dataset_repo),
) -> UploadService:
    return UploadService(storage, repo)


def get_cleaning_service(
    repo: DatasetRepository = Depends(get_dataset_repo),
    storage: StorageProtocol = Depends(get_storage),
    datasets: DatasetService = Depends(get_dataset_service),
) -> MockCleaningService:
    return MockCleaningService(repo, storage, datasets)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> UUID:
    """Decode JWT access token and return current user id."""
    if settings.dev_allow_anonymous:
        return UUID("00000000-0000-0000-0000-000000000001")
    if not credentials or credentials.scheme.lower() != "bearer":
        raise AppError.unauthorized("Missing or invalid Authorization header")
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except ValueError as exc:
        raise AppError.unauthorized("Invalid or expired token", code=ERR_AUTH_INVALID) from exc
    return UUID(str(payload["sub"]))


async def get_current_user_id(
    user_id: Annotated[UUID, Depends(get_current_user)],
) -> UUID:
    """Alias kept for existing dataset routes."""
    return user_id


async def require_project_access(
    project_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Session = Depends(get_db),
) -> UUID:
    """Ensure the current user owns the project (RBAC)."""
    project = db.get(Project, project_id)
    if project is None:
        raise AppError.not_found("Project not found", code=ERR_PROJECT_NOT_FOUND)
    if project.owner_id != user_id:
        raise AppError.forbidden("No access to this project", code=ERR_PROJECT_FORBIDDEN)
    return project_id
