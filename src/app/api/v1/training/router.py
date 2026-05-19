from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_project_access
from app.core.response import success
from app.schemas.training import TrainingJobCreate
from app.services.training_mock import MockTrainingService

training_service = MockTrainingService()

router = APIRouter(prefix="/projects/{project_id}/training-jobs", tags=["Training"])


@router.get("")
async def list_training_jobs(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    _: UUID = Depends(require_project_access),
):
    result = training_service.list_jobs(str(project_id), page, page_size, status)
    return success(result)


@router.post("")
async def create_training_job(
    project_id: UUID,
    body: TrainingJobCreate,
    _: UUID = Depends(require_project_access),
):
    data = body.model_dump()
    if isinstance(data.get("hyperparams"), dict):
        pass
    elif hasattr(body.hyperparams, "model_dump"):
        data["hyperparams"] = body.hyperparams.model_dump()

    job = training_service.create_job(str(project_id), data)

    from app.api.v1.experiments.router import experiment_service as exp_service

    exp_service.create_experiment(str(project_id), job["id"], job)

    return success(job)


@router.get("/{job_id}")
async def get_training_job(
    project_id: UUID,
    job_id: UUID,
    _: UUID = Depends(require_project_access),
):
    job = training_service.get_job(str(job_id))
    if not job or job.get("project_id") != str(project_id):
        from app.core.errors import ERR_TRAINING_JOB_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_TRAINING_JOB_NOT_FOUND, message=f"Training job '{job_id}' not found")
    return success(job)


@router.post("/{job_id}/start")
async def start_training(
    project_id: UUID,
    job_id: UUID,
    _: UUID = Depends(require_project_access),
):
    job = training_service.start_job(str(job_id))
    if not job:
        from app.core.errors import ERR_TRAINING_JOB_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_TRAINING_JOB_NOT_FOUND, message=f"Training job '{job_id}' not found")
    return success(job)


@router.post("/{job_id}/pause")
async def pause_training(
    project_id: UUID,
    job_id: UUID,
    _: UUID = Depends(require_project_access),
):
    job = training_service.pause_job(str(job_id))
    if not job:
        from app.core.errors import ERR_TRAINING_JOB_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_TRAINING_JOB_NOT_FOUND, message=f"Training job '{job_id}' not found")
    return success(job)


@router.post("/{job_id}/resume")
async def resume_training(
    project_id: UUID,
    job_id: UUID,
    _: UUID = Depends(require_project_access),
):
    job = training_service.resume_job(str(job_id))
    if not job:
        from app.core.errors import ERR_TRAINING_JOB_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_TRAINING_JOB_NOT_FOUND, message=f"Training job '{job_id}' not found")
    return success(job)


@router.post("/{job_id}/stop")
async def stop_training(
    project_id: UUID,
    job_id: UUID,
    _: UUID = Depends(require_project_access),
):
    job = training_service.stop_job(str(job_id))
    if not job:
        from app.core.errors import ERR_TRAINING_JOB_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_TRAINING_JOB_NOT_FOUND, message=f"Training job '{job_id}' not found")
    return success(job)


@router.get("/{job_id}/logs")
async def get_training_logs(
    project_id: UUID,
    job_id: UUID,
    tail: int = Query(200, ge=1, le=10000),
    _: UUID = Depends(require_project_access),
):
    job = training_service.get_job(str(job_id))
    if not job or job.get("project_id") != str(project_id):
        from app.core.errors import ERR_TRAINING_JOB_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_TRAINING_JOB_NOT_FOUND, message=f"Training job '{job_id}' not found")

    logs = training_service.get_logs(str(job_id), tail)
    return success({"logs": logs})


@router.get("/{job_id}/checkpoints")
async def list_checkpoints(
    project_id: UUID,
    job_id: UUID,
    _: UUID = Depends(require_project_access),
):
    job = training_service.get_job(str(job_id))
    if not job or job.get("project_id") != str(project_id):
        from app.core.errors import ERR_TRAINING_JOB_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_TRAINING_JOB_NOT_FOUND, message=f"Training job '{job_id}' not found")

    checkpoints = training_service.get_checkpoints(str(job_id))
    return success({"checkpoints": checkpoints})
