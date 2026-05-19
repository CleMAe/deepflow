from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_cleaning_service, require_project_access
from app.core.response import success
from app.schemas.cleaning import (
    CleanDedupRequest,
    CleanEncodeRequest,
    CleanMissingRequest,
    CleanOutlierRequest,
    CleanTypeConvertRequest,
)
from app.services.cleaning_mock import MockCleaningService

router = APIRouter(prefix="/projects/{project_id}/datasets/{ds_id}/clean", tags=["Datasets"])


@router.post("/missing")
async def clean_missing(
    project_id: UUID,
    ds_id: UUID,
    body: CleanMissingRequest,
    _: UUID = Depends(require_project_access),
    cleaning: MockCleaningService = Depends(get_cleaning_service),
):
    result = cleaning.run(project_id, ds_id, "missing")
    return success(result.model_dump(mode="json"))


@router.post("/outlier")
async def clean_outlier(
    project_id: UUID,
    ds_id: UUID,
    body: CleanOutlierRequest,
    _: UUID = Depends(require_project_access),
    cleaning: MockCleaningService = Depends(get_cleaning_service),
):
    result = cleaning.run(project_id, ds_id, "outlier")
    return success(result.model_dump(mode="json"))


@router.post("/dedup")
async def clean_dedup(
    project_id: UUID,
    ds_id: UUID,
    body: CleanDedupRequest,
    _: UUID = Depends(require_project_access),
    cleaning: MockCleaningService = Depends(get_cleaning_service),
):
    result = cleaning.run(project_id, ds_id, "dedup")
    return success(result.model_dump(mode="json"))


@router.post("/encode")
async def clean_encode(
    project_id: UUID,
    ds_id: UUID,
    body: CleanEncodeRequest,
    _: UUID = Depends(require_project_access),
    cleaning: MockCleaningService = Depends(get_cleaning_service),
):
    result = cleaning.run(project_id, ds_id, "encode")
    return success(result.model_dump(mode="json"))


@router.post("/type-convert")
async def clean_type_convert(
    project_id: UUID,
    ds_id: UUID,
    body: CleanTypeConvertRequest,
    _: UUID = Depends(require_project_access),
    cleaning: MockCleaningService = Depends(get_cleaning_service),
):
    result = cleaning.run(project_id, ds_id, "type-convert")
    return success(result.model_dump(mode="json"))
