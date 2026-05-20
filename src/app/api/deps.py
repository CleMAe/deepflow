"""FastAPI dependencies — Protocol implementations injected here (swap at integration)."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from shared.protocols import StorageProtocol

from app.core.config import settings
from app.core.errors import AppError
from app.db.session import get_db
from app.repositories.dataset_repository import DatasetRepository
from app.services.cleaning_mock import MockCleaningService
from app.services.dataset_service import DatasetService
from app.services.storage_mock import MockFileStorage
from app.services.training_service import TrainingService
from app.services.upload_service import UploadService

_bearer = HTTPBearer(auto_error=False)


@lru_cache
def get_storage() -> StorageProtocol:
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


def get_training_service(
    storage: StorageProtocol = Depends(get_storage),
) -> TrainingService:
    return TrainingService(storage)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> UUID:
    if settings.dev_allow_anonymous:
        return UUID("00000000-0000-0000-0000-000000000001")
    if not credentials or credentials.scheme.lower() != "bearer":
        raise AppError.unauthorized("Missing or invalid Authorization header")
    return UUID("00000000-0000-0000-0000-000000000001")


async def require_project_access(
    project_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> UUID:
    _ = user_id
    return project_id
