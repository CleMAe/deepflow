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
from app.core.security import decode_token
from app.db.session import get_db
from app.repositories.dataset_repository import DatasetRepository
from app.services.augmentation_service import PillowAugmentationService
from app.services.cleaning_engine import PandasCleaningEngine
from app.services.data_parser import PandasDataParser
from app.services.dataset_service import DatasetService
from app.services.eda_service import PandasEdaService
from app.services.storage_mock import MockFileStorage
from shared.protocols import DataParserProtocol
from app.services.training_service import TrainingService
from app.services.upload_service import UploadService

_bearer = HTTPBearer(auto_error=False)


@lru_cache
def get_storage() -> StorageProtocol:
    return MockFileStorage()


@lru_cache
def get_data_parser() -> DataParserProtocol:
    return PandasDataParser()


def get_dataset_repo(db: Session = Depends(get_db)) -> DatasetRepository:
    return DatasetRepository(db)


def get_dataset_service(
    repo: DatasetRepository = Depends(get_dataset_repo),
    storage: StorageProtocol = Depends(get_storage),
    parser: DataParserProtocol = Depends(get_data_parser),
) -> DatasetService:
    return DatasetService(repo, storage, parser)


def get_upload_service(
    storage: StorageProtocol = Depends(get_storage),
    repo: DatasetRepository = Depends(get_dataset_repo),
    parser: DataParserProtocol = Depends(get_data_parser),
) -> UploadService:
    return UploadService(storage, repo, parser)


def get_cleaning_service(
    repo: DatasetRepository = Depends(get_dataset_repo),
    storage: StorageProtocol = Depends(get_storage),
    parser: DataParserProtocol = Depends(get_data_parser),
) -> PandasCleaningEngine:
    return PandasCleaningEngine(repo, storage, parser)


def get_eda_service(
    repo: DatasetRepository = Depends(get_dataset_repo),
    parser: DataParserProtocol = Depends(get_data_parser),
) -> PandasEdaService:
    return PandasEdaService(repo, parser)


def get_augmentation_service(
    repo: DatasetRepository = Depends(get_dataset_repo),
    storage: StorageProtocol = Depends(get_storage),
) -> PillowAugmentationService:
    return PillowAugmentationService(repo, storage)


def get_training_service(
    storage: StorageProtocol = Depends(get_storage),
) -> TrainingService:
    return TrainingService(storage)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> UUID:
    if settings.dev_allow_anonymous and not credentials:
        return UUID("00000000-0000-0000-0000-000000000001")

    if not credentials or credentials.scheme.lower() != "bearer":
        raise AppError.unauthorized("Missing or invalid Authorization header")

    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        if settings.dev_allow_anonymous:
            return UUID("00000000-0000-0000-0000-000000000001")
        raise AppError.unauthorized("Invalid or expired token")

    if payload.get("type") != "access":
        raise AppError.unauthorized("Not an access token")

    return UUID(payload["sub"])


async def require_project_access(
    project_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Session = Depends(get_db),
) -> UUID:
    from src.infra.db.models.project import Project
    from app.core.errors import ERR_PROJECT_NOT_FOUND, ERR_PROJECT_FORBIDDEN

    project = db.get(Project, project_id)
    if not project:
        raise AppError.not_found("Project not found", code=ERR_PROJECT_NOT_FOUND)
    if project.owner_id != user_id:
        raise AppError.forbidden("Not your project", code=ERR_PROJECT_FORBIDDEN)
    return project_id
