from uuid import UUID, uuid4

from fastapi import APIRouter, Depends

from app.api.deps import get_dataset_service, require_project_access
from app.core.response import success
from app.schemas.eda import AugmentRequest, EdaRequest, SplitRequest, SplitResultSchema
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/projects/{project_id}/datasets/{ds_id}", tags=["Datasets"])


@router.post("/eda")
async def trigger_eda(
    project_id: UUID,
    ds_id: UUID,
    body: EdaRequest,
    _: UUID = Depends(require_project_access),
    svc: DatasetService = Depends(get_dataset_service),
):
    svc.get(project_id, ds_id)
    return success(
        {
            "dataset_id": str(ds_id),
            "status": "completed",
            "message": "EDA job queued (mock)",
            "include_visualizations": body.include_visualizations,
        }
    )


@router.get("/eda/report")
async def get_eda_report(
    project_id: UUID,
    ds_id: UUID,
    _: UUID = Depends(require_project_access),
    svc: DatasetService = Depends(get_dataset_service),
):
    svc.get(project_id, ds_id)
    return success(
        {
            "dataset_id": str(ds_id),
            "summary": {"num_rows": 150, "num_columns": 5, "num_missing": 0, "duplicate_rows": 0},
            "column_stats": [],
            "correlations": {},
            "visualizations": [],
            "created_at": "2026-05-19T00:00:00Z",
        }
    )


@router.post("/augment")
async def augment_dataset(
    project_id: UUID,
    ds_id: UUID,
    body: AugmentRequest,
    _: UUID = Depends(require_project_access),
    svc: DatasetService = Depends(get_dataset_service),
):
    source = svc.get(project_id, ds_id)
    return success(
        {
            "original_count": source.num_samples,
            "augmented_count": source.num_samples * body.num_augmented,
            "new_dataset_id": str(uuid4()),
            "output_dataset_name": body.output_dataset_name or f"{source.name}_aug",
        }
    )


@router.post("/split")
async def split_dataset(
    project_id: UUID,
    ds_id: UUID,
    body: SplitRequest,
    _: UUID = Depends(require_project_access),
    svc: DatasetService = Depends(get_dataset_service),
):
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
