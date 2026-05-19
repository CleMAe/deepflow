from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_project_access
from app.core.response import success
from app.schemas.experiment import CompareExperimentsRequest, ExperimentUpdate
from app.services.experiment_mock import MockExperimentService

experiment_service = MockExperimentService()

router = APIRouter(prefix="/projects/{project_id}/experiments", tags=["Experiments"])


@router.get("")
async def list_experiments(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: UUID = Depends(require_project_access),
):
    result = experiment_service.list_experiments(str(project_id), page, page_size)
    return success(result)


@router.get("/{exp_id}")
async def get_experiment(
    project_id: UUID,
    exp_id: UUID,
    _: UUID = Depends(require_project_access),
):
    exp = experiment_service.get_experiment(str(exp_id))
    if not exp or exp.get("project_id") != str(project_id):
        from app.core.errors import ERR_EXPERIMENT_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_EXPERIMENT_NOT_FOUND, message=f"Experiment '{exp_id}' not found")
    return success(exp)


@router.put("/{exp_id}")
async def update_experiment(
    project_id: UUID,
    exp_id: UUID,
    body: ExperimentUpdate,
    _: UUID = Depends(require_project_access),
):
    exp = experiment_service.update_experiment(str(exp_id), body.model_dump(exclude_none=True))
    if not exp:
        from app.core.errors import ERR_EXPERIMENT_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_EXPERIMENT_NOT_FOUND, message=f"Experiment '{exp_id}' not found")
    return success(exp)


@router.post("/compare")
async def compare_experiments(
    project_id: UUID,
    body: CompareExperimentsRequest,
    _: UUID = Depends(require_project_access),
):
    ids = [str(eid) for eid in body.experiment_ids]
    result = experiment_service.compare_experiments(ids)
    return success(result)
