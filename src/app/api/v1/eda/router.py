from uuid import UUID, uuid4

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_augmentation_service,
    get_dataset_service,
    get_eda_service,
    require_project_access,
)
from app.core.response import success
from app.schemas.eda import AugmentRequest, EdaRequest, SplitRequest, SplitResultSchema
from app.services.augmentation_service import PillowAugmentationService
from app.services.dataset_service import DatasetService
from app.services.eda_service import PandasEdaService

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
    svc: DatasetService = Depends(get_dataset_service),
):
    # Day3 placeholder: returns counts and UUIDs only; does not write split files to disk.
    source = svc.get(project_id, ds_id)
    n = source.num_samples or 100
    train_r = body.ratios.train
    val_r = body.ratios.val or 0.0
    test_r = body.ratios.test or max(0.0, 1.0 - train_r - val_r)
    train_n = int(n * train_r)
    val_n = int(n * val_r)
    test_n = n - train_n - val_n
    result = SplitResultSchema(
        train_dataset_id=uuid4(),
        val_dataset_id=uuid4() if val_r else None,
        test_dataset_id=uuid4() if test_r else None,
        train_count=train_n,
        val_count=val_n,
        test_count=test_n,
    )
    return success(result.model_dump(mode="json"))
