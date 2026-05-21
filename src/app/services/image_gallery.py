"""Image dataset gallery — scan raw dir, labels sidecar JSON."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from PIL import Image

_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
_LABELS_FILENAME = "labels.json"


def _dataset_root(file_path: str) -> Path:
    path = Path(file_path)
    return path if path.is_dir() else path.parent


def _list_image_paths(file_path: str) -> list[Path]:
    root = _dataset_root(file_path)
    if not root.is_dir():
        if root.is_file() and root.suffix.lower() in _IMAGE_SUFFIXES:
            return [root]
        return []
    return sorted(
        p for p in root.iterdir()
        if p.is_file() and p.suffix.lower() in _IMAGE_SUFFIXES
    )


def _labels_file(file_path: str) -> Path:
    return _dataset_root(file_path) / _LABELS_FILENAME


def load_labels_map(file_path: str) -> dict[str, list[str]]:
    labels_path = _labels_file(file_path)
    if not labels_path.is_file():
        return {}
    data = json.loads(labels_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    result: dict[str, list[str]] = {}
    for key, value in data.items():
        if isinstance(value, list):
            result[str(key)] = [str(v) for v in value]
        elif value is not None:
            result[str(key)] = [str(value)]
    return result


def save_labels_map(file_path: str, labels: dict[str, list[str]]) -> None:
    labels_path = _labels_file(file_path)
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    labels_path.write_text(json.dumps(labels, ensure_ascii=False, indent=2), encoding="utf-8")


def stable_image_id(project_id: uuid.UUID, dataset_id: uuid.UUID, filename: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"{project_id}:{dataset_id}:{filename}")


def image_dimensions(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as img:
            return img.size
    except Exception:
        return 0, 0
