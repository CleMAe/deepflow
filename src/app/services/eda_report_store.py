"""Persist EDA reports as JSON next to the dataset file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPORT_FILENAME = "eda_report.json"


def report_path_for_dataset(file_path: str) -> Path:
    path = Path(file_path)
    root = path if path.is_dir() else path.parent
    return root / _REPORT_FILENAME


def save_report(file_path: str, report: dict[str, Any]) -> None:
    out = report_path_for_dataset(file_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def load_report(file_path: str) -> dict[str, Any] | None:
    out = report_path_for_dataset(file_path)
    if not out.is_file():
        return None
    return json.loads(out.read_text(encoding="utf-8"))
