"""Unit tests for EDA report JSON persistence."""

from __future__ import annotations

from pathlib import Path

from app.services.eda_report_store import load_report, report_path_for_dataset, save_report


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    dataset_file = tmp_path / "data.csv"
    dataset_file.write_text("a,b\n1,2\n", encoding="utf-8")
    report = {"dataset_id": "ds-1", "summary": {"num_rows": 1}}

    save_report(str(dataset_file), report)

    out = report_path_for_dataset(str(dataset_file))
    assert out == tmp_path / "eda_report.json"
    assert out.is_file()
    assert load_report(str(dataset_file)) == report


def test_load_missing_returns_none(tmp_path: Path) -> None:
    assert load_report(str(tmp_path / "missing.csv")) is None
