"""
Experiment service — read tracking records tied to training jobs.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.schemas.experiment import ExperimentComparison, ExperimentOut, ExperimentUpdate
from src.infra.db.models.experiment import Experiment


def _exp_to_out(exp: Experiment) -> ExperimentOut:
    return ExperimentOut(
        id=str(exp.id),
        project_id=str(exp.project_id),
        job_id=str(exp.job_id),
        name=exp.name,
        metrics=exp.metrics,
        params_snap=exp.params_snap,
        tags=exp.tags or [],
        notes=exp.notes,
        created_at=exp.created_at.isoformat() if exp.created_at else None,
    )


class ExperimentService:
    def list_experiments(
        self, db: Session, project_id: uuid.UUID,
        page: int = 1, page_size: int = 20,
    ) -> dict:
        q = (
            select(Experiment)
            .where(Experiment.project_id == project_id)
            .order_by(Experiment.created_at.desc())
        )
        all_rows = db.scalars(
            select(Experiment).where(Experiment.project_id == project_id)
        ).all()
        total = len(all_rows)
        offset = (page - 1) * page_size
        rows = db.scalars(q.offset(offset).limit(page_size)).all()

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": [_exp_to_out(e).model_dump(mode="json") for e in rows],
        }

    def get_experiment(self, db: Session, project_id: uuid.UUID, exp_id: uuid.UUID) -> ExperimentOut:
        exp = db.get(Experiment, exp_id)
        if not exp or exp.project_id != project_id:
            raise AppError.not_found("Experiment not found")
        return _exp_to_out(exp)

    def update_experiment(
        self, db: Session, project_id: uuid.UUID, exp_id: uuid.UUID, payload: ExperimentUpdate,
    ) -> ExperimentOut:
        exp = db.get(Experiment, exp_id)
        if not exp or exp.project_id != project_id:
            raise AppError.not_found("Experiment not found")
        if payload.tags is not None:
            exp.tags = payload.tags
        if payload.notes is not None:
            exp.notes = payload.notes
        db.commit()
        db.refresh(exp)
        return _exp_to_out(exp)

    def compare_experiments(
        self, db: Session, project_id: uuid.UUID, experiment_ids: list[str],
    ) -> ExperimentComparison:
        uuids = [uuid.UUID(eid) for eid in experiment_ids]
        exps = db.scalars(
            select(Experiment)
            .where(Experiment.project_id == project_id, Experiment.id.in_(uuids))
        ).all()
        by_id = {e.id: e for e in exps}
        ordered_exps = [by_id[u] for u in uuids if u in by_id]

        exp_outs = [_exp_to_out(e) for e in ordered_exps]

        # Build metric comparison
        all_metrics: set[str] = set()
        for e in ordered_exps:
            if e.metrics and isinstance(e.metrics, dict):
                all_metrics.update(e.metrics.keys())

        metric_comparison: dict[str, list[float | None]] = {}
        for metric_name in sorted(all_metrics):
            metric_comparison[metric_name] = [
                (e.metrics or {}).get(metric_name) if isinstance(e.metrics, dict) else None
                for e in ordered_exps
            ]

        return ExperimentComparison(
            experiments=exp_outs,
            metric_comparison=metric_comparison,
        )
