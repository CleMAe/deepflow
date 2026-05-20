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
from app.services.cleaning_engine import PandasCleaningEngine

router = APIRouter(prefix="/projects/{project_id}/datasets/{ds_id}/clean", tags=["Cleaning"])


@router.post("/missing")
async def clean_missing(
    project_id: UUID,
    ds_id: UUID,
    body: CleanMissingRequest,
    _: UUID = Depends(require_project_access),
    cleaning: PandasCleaningEngine = Depends(get_cleaning_service),
):
    result = cleaning.handle_missing(project_id, ds_id, body)
    return success(result.model_dump(mode="json"))


@router.post("/outlier")
async def clean_outlier(
    project_id: UUID,
    ds_id: UUID,
    body: CleanOutlierRequest,
    _: UUID = Depends(require_project_access),
    cleaning: PandasCleaningEngine = Depends(get_cleaning_service),
):
    result = cleaning.detect_outliers(project_id, ds_id, body)
    return success(result.model_dump(mode="json"))


@router.post("/dedup")
async def clean_dedup(
    project_id: UUID,
    ds_id: UUID,
    body: CleanDedupRequest,
    _: UUID = Depends(require_project_access),
    cleaning: PandasCleaningEngine = Depends(get_cleaning_service),
):
    result = cleaning.deduplicate(project_id, ds_id, body)
    return success(result.model_dump(mode="json"))


@router.post("/encode")
async def clean_encode(
    project_id: UUID,
    ds_id: UUID,
    body: CleanEncodeRequest,
    _: UUID = Depends(require_project_access),
    cleaning: PandasCleaningEngine = Depends(get_cleaning_service),
):
    result = cleaning.encode(project_id, ds_id, body)
    return success(result.model_dump(mode="json"))


@router.post("/type-convert")
async def clean_type_convert(
    project_id: UUID,
    ds_id: UUID,
    body: CleanTypeConvertRequest,
    _: UUID = Depends(require_project_access),
    cleaning: PandasCleaningEngine = Depends(get_cleaning_service),
):
    result = cleaning.type_convert(project_id, ds_id, body)
    return success(result.model_dump(mode="json"))
