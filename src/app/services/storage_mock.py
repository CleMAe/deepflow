"""Mock implementation of `StorageProtocol` for parallel dev before P6 RealFileStorage."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from app.core.config import settings
from shared.protocols import StorageProtocol


class MockFileStorage(StorageProtocol):
    """File-system storage; paths follow P6 layout under STORAGE_ROOT."""

    def __init__(self, root: str | None = None) -> None:
        self._root = Path(root or settings.storage_root)
        self._root.mkdir(parents=True, exist_ok=True)
        (self._root / "uploads").mkdir(exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def get_project_path(self, project_id: str) -> str:
        path = self._root / "projects" / project_id
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_dataset_path(self, project_id: str, dataset_id: str) -> str:
        path = Path(self.get_project_path(project_id)) / "datasets" / dataset_id
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_raw_path(self, project_id: str, dataset_id: str) -> str:
        path = Path(self.get_dataset_path(project_id, dataset_id)) / "raw"
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_cleaned_path(self, project_id: str, dataset_id: str) -> str:
        path = Path(self.get_dataset_path(project_id, dataset_id)) / "cleaned"
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_model_path(self, project_id: str, model_id: str) -> str:
        path = Path(self.get_project_path(project_id)) / "models" / model_id
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_checkpoint_path(self, project_id: str, model_id: str) -> str:
        path = Path(self.get_model_path(project_id, model_id)) / "checkpoint"
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_exported_path(self, project_id: str, model_id: str) -> str:
        path = Path(self.get_model_path(project_id, model_id)) / "exported"
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_experiment_path(self, project_id: str, experiment_id: str) -> str:
        path = Path(self.get_project_path(project_id)) / "experiments" / experiment_id
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def ensure_dir(self, path: str) -> str:
        Path(path).mkdir(parents=True, exist_ok=True)
        return path

    def get_upload_temp_path(self) -> str:
        path = self._root / "uploads" / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_storage_usage(self, project_id: str) -> int:
        base = Path(self.get_project_path(project_id))
        total = 0
        for dirpath, _, filenames in os.walk(base):
            for name in filenames:
                total += (Path(dirpath) / name).stat().st_size
        return total
