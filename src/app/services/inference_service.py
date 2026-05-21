"""
Inference service — business logic layer for model inference.

Validates model/dataset existence, resolves checkpoints, delegates
to InferenceEngine for actual PyTorch inference, manages async tasks.
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import (
    ERR_INFERENCE_CHECKPOINT_NOT_FOUND,
    ERR_INFERENCE_DATASET_NOT_FOUND,
    ERR_INFERENCE_EXPORT_FAILED,
    ERR_INFERENCE_MODEL_LOAD_FAILED,
    ERR_INFERENCE_MODEL_NOT_FOUND,
    ERR_INFERENCE_TASK_NOT_FOUND,
    AppError,
)
from app.schemas.inference import (
    EvaluateResult,
    ExportOnnxResult,
    InferenceTaskResponse,
    OnlineInferenceResult,
    PredictionItem,
)
from src.engine.inference_engine import InferenceEngine
from src.infra.db.models.dataset import Dataset
from src.infra.db.models.ml_model import MLModel
from src.infra.db.models.training_job import TrainingJob, TrainingJobStatus
from src.shared.protocols import StorageProtocol

_VALID_OUTPUT_FORMATS = {"json", "csv"}


@lru_cache(maxsize=1)
def _get_engine() -> InferenceEngine:
    return InferenceEngine()


class InferenceService:
    def __init__(self, storage: StorageProtocol) -> None:
        self._storage = storage

    def _get_model(self, db: Session, project_id: uuid.UUID, model_id: uuid.UUID) -> MLModel:
        model = db.get(MLModel, model_id)
        if not model or model.project_id != project_id:
            raise AppError.not_found("Model not found", code=ERR_INFERENCE_MODEL_NOT_FOUND)
        return model

    def _get_dataset(self, db: Session, project_id: uuid.UUID, dataset_id: uuid.UUID) -> Dataset:
        ds = db.get(Dataset, dataset_id)
        if not ds or ds.project_id != project_id:
            raise AppError.not_found("Dataset not found", code=ERR_INFERENCE_DATASET_NOT_FOUND)
        return ds

    def _resolve_checkpoint(
        self,
        db: Session,
        project_id: uuid.UUID,
        model: MLModel,
        checkpoint_path: str | None,
    ) -> str:
        """Resolve checkpoint path: explicit > best from training job > model_path."""
        engine = _get_engine()

        if checkpoint_path:
            return checkpoint_path

        job = db.scalars(
            select(TrainingJob)
            .where(
                TrainingJob.model_id == model.id,
                TrainingJob.status == TrainingJobStatus.SUCCESS,
            )
            .order_by(TrainingJob.finished_at.desc())
            .limit(1)
        ).first()

        if job and job.checkpoint:
            return job.checkpoint

        resolved = engine.find_checkpoint(checkpoint_path, model.model_path)
        if resolved:
            return resolved

        raise AppError.not_found(
            "No checkpoint found for this model. Train the model first or provide checkpoint_path.",
            code=ERR_INFERENCE_CHECKPOINT_NOT_FOUND,
        )

    def _resolve_dataset_path(self, ds: Dataset, project_id: uuid.UUID) -> str:
        """Resolve the actual file path for a dataset."""
        if ds.file_path:
            return ds.file_path
        return self._storage.get_raw_path(str(project_id), str(ds.id))

    # ── Online inference ─────────────────────────────────────────

    def online_inference(
        self,
        db: Session,
        project_id: uuid.UUID,
        model_id: uuid.UUID,
        input_data: dict[str, Any] | str,
        checkpoint_path: str | None = None,
    ) -> OnlineInferenceResult:
        engine = _get_engine()
        model = self._get_model(db, project_id, model_id)
        ckpt_path = self._resolve_checkpoint(db, project_id, model, checkpoint_path)

        try:
            result = engine.online_inference(ckpt_path, input_data)
        except FileNotFoundError as e:
            raise AppError.not_found(str(e), code=ERR_INFERENCE_CHECKPOINT_NOT_FOUND)
        except Exception as e:
            raise AppError.internal(f"Model inference failed: {e}", code=ERR_INFERENCE_MODEL_LOAD_FAILED)

        return OnlineInferenceResult(
            prediction=result["prediction"],
            confidence=result.get("confidence"),
            probabilities=result.get("probabilities"),
            latency_ms=result.get("latency_ms"),
        )

    # ── Evaluate ─────────────────────────────────────────────────

    def evaluate(
        self,
        db: Session,
        project_id: uuid.UUID,
        model_id: uuid.UUID,
        dataset_id: uuid.UUID,
        checkpoint_path: str | None = None,
        metrics: list[str] | None = None,
    ) -> EvaluateResult:
        engine = _get_engine()
        model = self._get_model(db, project_id, model_id)
        ds = self._get_dataset(db, project_id, dataset_id)
        ckpt_path = self._resolve_checkpoint(db, project_id, model, checkpoint_path)
        ds_path = self._resolve_dataset_path(ds, project_id)

        try:
            result = engine.evaluate(ckpt_path, ds_path, model.arch_type, metrics)
        except FileNotFoundError as e:
            raise AppError.not_found(str(e), code=ERR_INFERENCE_CHECKPOINT_NOT_FOUND)
        except Exception as e:
            raise AppError.internal(f"Evaluation failed: {e}", code=ERR_INFERENCE_MODEL_LOAD_FAILED)

        return EvaluateResult(
            model_id=str(model_id),
            dataset_id=str(dataset_id),
            metrics=result.get("metrics", {}),
            confusion_matrix=result.get("confusion_matrix"),
            classification_report=result.get("classification_report"),
            num_samples=result.get("num_samples", 0),
        )

    # ── Batch inference ──────────────────────────────────────────

    def start_batch_inference(
        self,
        db: Session,
        project_id: uuid.UUID,
        model_id: uuid.UUID,
        dataset_id: uuid.UUID,
        checkpoint_path: str | None = None,
        output_format: str = "json",
    ) -> InferenceTaskResponse:
        if output_format not in _VALID_OUTPUT_FORMATS:
            from app.core.errors import ERR_INFERENCE_INVALID_PARAM
            raise AppError.bad_request(
                f"Unsupported output_format '{output_format}'. Must be one of {sorted(_VALID_OUTPUT_FORMATS)}.",
                code=ERR_INFERENCE_INVALID_PARAM,
            )

        engine = _get_engine()
        model = self._get_model(db, project_id, model_id)
        ds = self._get_dataset(db, project_id, dataset_id)
        ckpt_path = self._resolve_checkpoint(db, project_id, model, checkpoint_path)
        ds_path = self._resolve_dataset_path(ds, project_id)

        task_id = engine.create_task(str(model_id))

        output_dir = self._storage.get_exported_path(str(project_id), str(model_id))

        thread = threading.Thread(
            target=engine.run_batch_inference,
            kwargs={
                "task_id": task_id,
                "checkpoint_path": ckpt_path,
                "dataset_path": ds_path,
                "arch_type": model.arch_type,
                "output_dir": output_dir,
            },
            daemon=True,
        )
        thread.start()

        task = engine.get_task(task_id)
        return self._task_to_response(task)

    # ── Get inference task ───────────────────────────────────────

    def get_inference_result(
        self,
        db: Session,
        project_id: uuid.UUID,
        task_id: str,
    ) -> InferenceTaskResponse:
        engine = _get_engine()
        task = engine.get_task(task_id)
        if not task:
            raise AppError.not_found("Inference task not found", code=ERR_INFERENCE_TASK_NOT_FOUND)
        return self._task_to_response(task)

    # ── Export ONNX ──────────────────────────────────────────────

    def export_onnx(
        self,
        db: Session,
        project_id: uuid.UUID,
        model_id: uuid.UUID,
        checkpoint_path: str | None = None,
        opset_version: int = 17,
        dynamic_batch: bool = True,
    ) -> ExportOnnxResult:
        engine = _get_engine()
        model = self._get_model(db, project_id, model_id)
        ckpt_path = self._resolve_checkpoint(db, project_id, model, checkpoint_path)

        output_dir = self._storage.get_exported_path(str(project_id), str(model_id))
        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
        onnx_path = f"{output_dir}/model_{ts}.onnx"

        try:
            engine.export_onnx(
                checkpoint_path=ckpt_path,
                output_path=onnx_path,
                opset_version=opset_version,
                dynamic_batch=dynamic_batch,
            )
        except FileNotFoundError as e:
            raise AppError.not_found(str(e), code=ERR_INFERENCE_CHECKPOINT_NOT_FOUND)
        except Exception as e:
            raise AppError.internal(f"ONNX export failed: {e}", code=ERR_INFERENCE_EXPORT_FAILED)

        if not model.model_path:
            model.model_path = onnx_path
            db.commit()

        return ExportOnnxResult(
            onnx_path=onnx_path,
            status="ready",
            opset_version=opset_version,
        )

    # ── Helpers ──────────────────────────────────────────────────

    def _task_to_response(self, task: dict[str, Any]) -> InferenceTaskResponse:
        predictions = None
        if task.get("predictions"):
            predictions = [
                PredictionItem(prediction=p.get("prediction"), confidence=p.get("confidence"))
                for p in task["predictions"]
            ]

        created_at = None
        if task.get("created_at"):
            created_at = datetime.fromtimestamp(task["created_at"], tz=timezone.utc).isoformat()

        finished_at = None
        if task.get("finished_at"):
            finished_at = datetime.fromtimestamp(task["finished_at"], tz=timezone.utc).isoformat()

        return InferenceTaskResponse(
            task_id=task["task_id"],
            model_id=task.get("model_id"),
            status=task.get("status", "pending"),
            progress=task.get("progress"),
            result_path=task.get("result_path"),
            predictions=predictions,
            created_at=created_at,
            finished_at=finished_at,
        )
