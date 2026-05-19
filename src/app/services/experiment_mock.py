from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class MockExperimentService:
    def __init__(self) -> None:
        self._experiments: dict[str, dict[str, Any]] = {}

    def list_experiments(
        self, project_id: str, page: int = 1, page_size: int = 20
    ) -> dict[str, Any]:
        project_exps = [
            e
            for e in self._experiments.values()
            if e.get("project_id") == project_id
        ]
        total = len(project_exps)
        start = (page - 1) * page_size
        items = project_exps[start : start + page_size]
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": items,
        }

    def get_experiment(self, exp_id: str) -> dict[str, Any] | None:
        return self._experiments.get(exp_id)

    def create_experiment(
        self, project_id: str, job_id: str, job_data: dict[str, Any]
    ) -> dict[str, Any]:
        exp_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        exp = {
            "id": exp_id,
            "project_id": project_id,
            "job_id": job_id,
            "name": job_data.get("name", "Untitled Experiment"),
            "metrics": job_data.get("metrics", {}),
            "params_snap": job_data.get("hyperparams", {}),
            "tags": [],
            "notes": None,
            "created_at": now,
        }
        self._experiments[exp_id] = exp
        return exp

    def update_experiment(
        self, exp_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        exp = self._experiments.get(exp_id)
        if not exp:
            return None
        if "tags" in data and data["tags"] is not None:
            exp["tags"] = data["tags"]
        if "notes" in data and data["notes"] is not None:
            exp["notes"] = data["notes"]
        return exp

    def compare_experiments(
        self, experiment_ids: list[str]
    ) -> dict[str, Any]:
        experiments = []
        metric_comparison: dict[str, list[float]] = {}
        param_diff: dict[str, Any] = {}

        for exp_id in experiment_ids:
            exp = self._experiments.get(exp_id)
            if exp:
                experiments.append(exp)
                if exp.get("metrics"):
                    for k, v in exp["metrics"].items():
                        if isinstance(v, (int, float)):
                            metric_comparison.setdefault(k, []).append(float(v))

        return {
            "experiments": experiments,
            "metric_comparison": metric_comparison,
            "param_diff": param_diff,
        }
