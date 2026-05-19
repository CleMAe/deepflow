from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.schemas.training import CheckpointSchema


class MockTrainingService:
    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._logs: dict[str, list[str]] = {}
        self._checkpoints: dict[str, list[dict[str, Any]]] = {}

    def list_jobs(
        self,
        project_id: str,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> dict[str, Any]:
        project_jobs = [
            j for j in self._jobs.values() if j.get("project_id") == project_id
        ]
        if status:
            project_jobs = [j for j in project_jobs if j.get("status") == status]
        total = len(project_jobs)
        start = (page - 1) * page_size
        items = project_jobs[start : start + page_size]
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": items,
        }

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self._jobs.get(job_id)

    def create_job(self, project_id: str, data: dict[str, Any]) -> dict[str, Any]:
        job_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        job = {
            "id": job_id,
            "project_id": project_id,
            "name": data.get("name", "Untitled Job"),
            "model_id": str(data.get("model_id", "")),
            "dataset_id": str(data.get("dataset_id", "")),
            "val_dataset_id": str(data["val_dataset_id"]) if data.get("val_dataset_id") else None,
            "hyperparams": data.get("hyperparams"),
            "status": "pending",
            "device": data.get("device", "auto"),
            "current_epoch": 0,
            "total_epochs": None,
            "metrics": None,
            "checkpoint": None,
            "error_message": None,
            "description": data.get("description"),
            "started_at": None,
            "finished_at": None,
            "created_at": now,
            "updated_at": now,
        }
        if isinstance(data.get("hyperparams"), dict):
            job["total_epochs"] = data["hyperparams"].get("epochs")
        self._jobs[job_id] = job
        self._logs[job_id] = [
            f"[{now}] Job '{job['name']}' created. Status: pending",
        ]
        self._checkpoints[job_id] = []
        return job

    def start_job(self, job_id: str) -> dict[str, Any] | None:
        job = self._jobs.get(job_id)
        if not job:
            return None
        if job["status"] not in ("pending", "paused"):
            return job
        now = datetime.now(timezone.utc).isoformat()
        job["status"] = "running"
        job["started_at"] = job["started_at"] or now
        job["updated_at"] = now
        self._logs.setdefault(job_id, []).append(
            f"[{now}] Training started. Device: {job.get('device', 'auto')}"
        )
        return job

    def pause_job(self, job_id: str) -> dict[str, Any] | None:
        job = self._jobs.get(job_id)
        if not job or job["status"] != "running":
            return job
        now = datetime.now(timezone.utc).isoformat()
        job["status"] = "paused"
        job["updated_at"] = now
        self._logs.setdefault(job_id, []).append(
            f"[{now}] Training paused at epoch {job.get('current_epoch', 0)}"
        )
        return job

    def resume_job(self, job_id: str) -> dict[str, Any] | None:
        job = self._jobs.get(job_id)
        if not job or job["status"] != "paused":
            return job
        now = datetime.now(timezone.utc).isoformat()
        job["status"] = "running"
        job["updated_at"] = now
        self._logs.setdefault(job_id, []).append(
            f"[{now}] Training resumed"
        )
        return job

    def stop_job(self, job_id: str) -> dict[str, Any] | None:
        job = self._jobs.get(job_id)
        if not job or job["status"] not in ("running", "paused"):
            return job
        now = datetime.now(timezone.utc).isoformat()
        job["status"] = "cancelled"
        job["finished_at"] = now
        job["updated_at"] = now
        self._logs.setdefault(job_id, []).append(
            f"[{now}] Training cancelled"
        )
        return job

    def get_logs(self, job_id: str, tail: int = 200) -> list[str]:
        logs = self._logs.get(job_id, [])
        return logs[-tail:]

    def get_checkpoints(self, job_id: str) -> list[dict[str, Any]]:
        return self._checkpoints.get(job_id, [])
