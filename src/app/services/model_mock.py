import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.schemas.model import (
    LibraryModelSchema,
    ValidationResultSchema,
)


class MockModelLibrary:
    def __init__(self) -> None:
        data_path = Path(__file__).parent.parent / "data" / "model_library.json"
        with open(data_path) as f:
            self._models: list[dict[str, Any]] = json.load(f)

    def list_models(
        self, task_type: str | None = None, search: str | None = None
    ) -> list[dict[str, Any]]:
        result = self._models
        if task_type:
            result = [m for m in result if m["task_type"] == task_type]
        if search:
            q = search.lower()
            result = [
                m
                for m in result
                if q in m["name"].lower() or q in m["model_id"].lower() or q in m.get("description", "").lower()
            ]
        return result

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        for m in self._models:
            if m["model_id"] == model_id:
                return m
        return None

    def get_default_hyperparams(self, arch_type: str) -> dict[str, Any]:
        for m in self._models:
            if m["arch_type"] == arch_type:
                return m.get("default_hyperparams", {})
        return {}

    def validate_config(
        self, arch_type: str, params_cfg: dict[str, Any]
    ) -> ValidationResultSchema:
        model = self.get_model(arch_type)
        if not model:
            for m in self._models:
                if m["arch_type"] == arch_type:
                    model = m
                    break

        errors: list[dict[str, str]] = []
        warnings: list[dict[str, str]] = []

        if arch_type not in {"resnet18", "resnet34", "resnet50", "efficientnet_b0", "efficientnet_b3", "mlp", "custom"}:
            errors.append({"field": "arch_type", "message": f"Unknown architecture: {arch_type}"})

        if not params_cfg:
            warnings.append({"field": "params_cfg", "message": "Empty config, defaults will be used"})

        return ValidationResultSchema(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


class MockModelService:
    def __init__(self) -> None:
        self._models: dict[str, dict[str, Any]] = {}
        self._library = MockModelLibrary()

    def list_project_models(
        self, project_id: str, page: int = 1, page_size: int = 20
    ) -> dict[str, Any]:
        project_models = [
            m for m in self._models.values() if m.get("project_id") == project_id
        ]
        total = len(project_models)
        start = (page - 1) * page_size
        items = project_models[start : start + page_size]
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": items,
        }

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        return self._models.get(model_id)

    def create_model(self, project_id: str, data: dict[str, Any]) -> dict[str, Any]:
        model_id = str(uuid4())
        model = {
            "id": model_id,
            "project_id": project_id,
            "name": data.get("name", "Untitled Model"),
            "arch_type": data.get("arch_type", "mlp"),
            "params_cfg": data.get("params_cfg"),
            "pretrained": False,
            "pretrained_source": None,
            "model_path": None,
            "description": data.get("description"),
            "created_at": "2026-05-19T10:00:00Z",
            "updated_at": "2026-05-19T10:00:00Z",
        }
        self._models[model_id] = model
        return model

    def update_model(
        self, model_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        if model_id not in self._models:
            return None
        model = self._models[model_id]
        for key in ("name", "params_cfg", "description"):
            if key in data and data[key] is not None:
                model[key] = data[key]
        model["updated_at"] = "2026-05-19T10:30:00Z"
        return model

    def get_model_library(self) -> MockModelLibrary:
        return self._library
