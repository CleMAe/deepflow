from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_augmentation_service,
    get_eda_service,
    get_split_service,
    require_project_access,
)
from app.core.response import success
from app.schemas.eda import AugmentRequest, EdaRequest, SplitRequest
from app.services.augmentation_service import PillowAugmentationService
from app.services.eda_service import PandasEdaService
from app.services.split_service import PandasSplitService

router = APIRouter(prefix="/projects/{project_id}/datasets/{ds_id}", tags=["EDA"])


@router.post("/eda")
async def trigger_eda(
    project_id: UUID,
    ds_id: UUID,
    body: EdaRequest,
    _: UUID = Depends(require_project_access),
    eda: PandasEdaService = Depends(get_eda_service),
):
    report = eda.run_eda(project_id, ds_id, body)
    return success(
        {
            "dataset_id": report["dataset_id"],
            "status": "completed",
            "message": "EDA completed",
            "include_visualizations": body.include_visualizations,
        }
    )


@router.get("/eda/report")
async def get_eda_report(
    project_id: UUID,
    ds_id: UUID,
    _: UUID = Depends(require_project_access),
    eda: PandasEdaService = Depends(get_eda_service),
):
    return success(eda.get_report(project_id, ds_id))


@router.post("/augment")
async def augment_dataset(
    project_id: UUID,
    ds_id: UUID,
    body: AugmentRequest,
    _: UUID = Depends(require_project_access),
    augment: PillowAugmentationService = Depends(get_augmentation_service),
):
    result = augment.augment(project_id, ds_id, body)
    return success(result)


@router.post("/split")
async def split_dataset(
    project_id: UUID,
    ds_id: UUID,
    body: SplitRequest,
    _: UUID = Depends(require_project_access),
    split_svc: PandasSplitService = Depends(get_split_service),
):
    result = split_svc.split(project_id, ds_id, body)
    return success(result.model_dump(mode="json"))
