"""
Training service — state machine enforcement, DB persistence,
and subprocess lifecycle management via TrainingEngineManager.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.engine.manager import TrainingEngineManager
from src.infra.db.models.ml_model import MLModel
from src.infra.db.models.training_job import TrainingJob, TrainingJobStatus
from src.shared.protocols import StorageProtocol

from app.core.errors import AppError, ERR_TRAINING_JOB_NOT_FOUND, ERR_TRAINING_INVALID_TRANSITION, ERR_MODEL_NOT_FOUND
from app.schemas.training import TrainingJobCreate, TrainingJobOut, CheckpointOut, TrainingLogOut

# State machine: valid transitions
_VALID_TRANSITIONS: dict[TrainingJobStatus, set[TrainingJobStatus]] = {
    TrainingJobStatus.PENDING: {TrainingJobStatus.RUNNING, TrainingJobStatus.CANCELLED},
    TrainingJobStatus.RUNNING: {TrainingJobStatus.PAUSED, TrainingJobStatus.SUCCESS, TrainingJobStatus.FAILED, TrainingJobStatus.CANCELLED},
    TrainingJobStatus.PAUSED: {TrainingJobStatus.RUNNING, TrainingJobStatus.CANCELLED},
    TrainingJobStatus.SUCCESS: set(),
    TrainingJobStatus.FAILED: set(),
    TrainingJobStatus.CANCELLED: set(),
}

_engine = TrainingEngineManager()


def _job_to_out(job: TrainingJob) -> TrainingJobOut:
    from app.schemas.training import TrainingMetrics

    metrics = job.metrics if isinstance(job.metrics, dict) else {}

    return TrainingJobOut(
        id=str(job.id),
        project_id=str(job.project_id),
        name=job.name,
        model_id=str(job.model_id),
        dataset_id=str(job.dataset_id),
        val_dataset_id=str(job.val_dataset_id) if job.val_dataset_id else None,
        hyperparams=job.hyperparams,
        status=job.status.value if isinstance(job.status, TrainingJobStatus) else str(job.status),
        device=job.device,
        current_epoch=job.current_epoch,
        total_epochs=job.total_epochs,
        metrics=TrainingMetrics(**metrics) if metrics else TrainingMetrics(),
        checkpoint=job.checkpoint,
        error_message=job.error_message,
        description=job.description,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        created_at=job.created_at.isoformat() if job.created_at else None,
        updated_at=job.updated_at.isoformat() if job.updated_at else None,
    )


class TrainingService:
    def __init__(self, storage: StorageProtocol) -> None:
        self._storage = storage

    def create_job(self, db: Session, project_id: uuid.UUID, payload: TrainingJobCreate) -> TrainingJobOut:
        model = db.get(MLModel, uuid.UUID(payload.model_id))
        if not model or model.project_id != project_id:
            raise AppError.not_found("Model not found", code=ERR_MODEL_NOT_FOUND)

        hp = payload.hyperparams.model_dump(mode="json")
        job = TrainingJob(
            project_id=project_id,
            name=payload.name,
            model_id=uuid.UUID(payload.model_id),
            dataset_id=uuid.UUID(payload.dataset_id),
            val_dataset_id=uuid.UUID(payload.val_dataset_id) if payload.val_dataset_id else None,
            hyperparams=hp,
            status=TrainingJobStatus.PENDING,
            device=payload.device,
            total_epochs=hp.get("epochs", 10),
            description=payload.description,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return _job_to_out(job)

    def list_jobs(
        self, db: Session, project_id: uuid.UUID,
        page: int = 1, page_size: int = 20, status: str | None = None,
    ) -> dict:
        base = select(TrainingJob).where(TrainingJob.project_id == project_id)
        if status:
            try:
                base = base.where(TrainingJob.status == TrainingJobStatus(status))
            except ValueError:
                pass

        total = db.scalar(select(func.count()).select_from(base.subquery()))
        offset = (page - 1) * page_size
        rows = db.scalars(
            base.order_by(TrainingJob.created_at.desc()).offset(offset).limit(page_size)
        ).all()

        return {
            "page": page,
            "page_size": page_size,
            "total": total or 0,
            "items": [_job_to_out(j).model_dump(mode="json") for j in rows],
        }

    def get_job(self, db: Session, project_id: uuid.UUID, job_id: uuid.UUID) -> TrainingJobOut:
        job = self._get_and_check(db, project_id, job_id)

        # Sync subprocess status into DB
        progress = _engine.get_progress(str(job_id))
        if progress:
            job.current_epoch = progress.get("current_epoch", job.current_epoch)
            job.metrics = {
                "train_loss": progress.get("train_loss"),
                "val_loss": progress.get("val_loss"),
                "accuracy": progress.get("accuracy"),
                "best_val_loss": progress.get("best_val_loss"),
                "best_accuracy": progress.get("best_accuracy"),
            }
            if progress.get("checkpoint_path"):
                job.checkpoint = progress["checkpoint_path"]
            if progress.get("error_message") and progress["status"] == "failed":
                job.error_message = progress["error_message"]

            engine_status = progress.get("status")
            if engine_status and engine_status != job.status.value:
                try:
                    new_status = TrainingJobStatus(engine_status)
                    job.status = new_status
                    if new_status in (TrainingJobStatus.SUCCESS, TrainingJobStatus.FAILED, TrainingJobStatus.CANCELLED):
                        job.finished_at = datetime.now(timezone.utc)
                except ValueError:
                    pass

            db.commit()
            db.refresh(job)

        return _job_to_out(job)

    def start_job(self, db: Session, project_id: uuid.UUID, job_id: uuid.UUID) -> TrainingJobOut:
        job = self._get_and_check(db, project_id, job_id)
        self._transition(job, TrainingJobStatus.RUNNING)

        job.started_at = datetime.now(timezone.utc)

        model = db.get(MLModel, job.model_id)
        arch_type = model.arch_type if model else "mlp"
        dataset_path = self._storage.get_raw_path(str(project_id), str(job.dataset_id))
        checkpoint_dir = self._storage.get_checkpoint_path(str(project_id), str(job.model_id))
        val_path = None
        if job.val_dataset_id:
            val_path = self._storage.get_raw_path(str(project_id), str(job.val_dataset_id))

        _engine.start_training(
            job_id=str(job_id),
            model_arch=arch_type,
            dataset_path=dataset_path,
            output_dir=checkpoint_dir,
            val_dataset_path=val_path,
            hyperparams=job.hyperparams or {},
            device=job.device or "auto",
        )

        db.commit()
        db.refresh(job)
        return _job_to_out(job)

    def pause_job(self, db: Session, project_id: uuid.UUID, job_id: uuid.UUID) -> TrainingJobOut:
        job = self._get_and_check(db, project_id, job_id)
        self._transition(job, TrainingJobStatus.PAUSED)
        _engine.pause_training(str(job_id))
        db.commit()
        db.refresh(job)
        return _job_to_out(job)

    def resume_job(self, db: Session, project_id: uuid.UUID, job_id: uuid.UUID) -> TrainingJobOut:
        job = self._get_and_check(db, project_id, job_id)
        self._transition(job, TrainingJobStatus.RUNNING)
        _engine.resume_training(str(job_id))
        db.commit()
        db.refresh(job)
        return _job_to_out(job)

    def stop_job(self, db: Session, project_id: uuid.UUID, job_id: uuid.UUID) -> TrainingJobOut:
        job = self._get_and_check(db, project_id, job_id)
        self._transition(job, TrainingJobStatus.CANCELLED)
        _engine.stop_training(str(job_id))
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        return _job_to_out(job)

    def get_checkpoints(self, db: Session, project_id: uuid.UUID, job_id: uuid.UUID) -> list[CheckpointOut]:
        job = self._get_and_check(db, project_id, job_id)
        checkpoint_dir = self._storage.get_checkpoint_path(str(project_id), str(job.model_id))
        raw = _engine.get_checkpoints(str(job_id), checkpoint_dir)
        return [CheckpointOut(**c) for c in raw]

    def get_logs(self, db: Session, project_id: uuid.UUID, job_id: uuid.UUID, tail: int = 200) -> TrainingLogOut:
        self._get_and_check(db, project_id, job_id)
        lines = _engine.get_logs(str(job_id), tail)
        return TrainingLogOut(logs=lines)

    def _get_and_check(self, db: Session, project_id: uuid.UUID, job_id: uuid.UUID) -> TrainingJob:
        job = db.get(TrainingJob, job_id)
        if not job or job.project_id != project_id:
            raise AppError.not_found("Training job not found", code=ERR_TRAINING_JOB_NOT_FOUND)
        return job

    def _transition(self, job: TrainingJob, target: TrainingJobStatus) -> None:
        current = job.status
        if target not in _VALID_TRANSITIONS.get(current, set()):
            raise AppError.bad_request(
                f"Cannot transition from {current.value} to {target.value}",
                code=ERR_TRAINING_INVALID_TRANSITION,
            )
        job.status = target
