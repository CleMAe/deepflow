"""Unit tests for encoding methods in PandasCleaningEngine."""

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.core.errors import ERR_DATASET_INVALID_PARAM, AppError
from app.schemas.cleaning import CleanEncodeRequest
from app.services.cleaning_engine import PandasCleaningEngine


def _make_engine_with_csv(tmp_path: Path, df: pd.DataFrame) -> tuple[PandasCleaningEngine, uuid.UUID, uuid.UUID]:
    project_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    csv_path = tmp_path / "data.csv"
    df.to_csv(csv_path, index=False)

    row = MagicMock()
    row.id = dataset_id
    row.name = "test"
    row.file_path = str(csv_path)
    row.format = MagicMock(value="csv")
    row.tags = []

    repo = MagicMock()
    repo.get_by_id_and_project.return_value = row
    storage = MagicMock()
    storage.get_raw_path.return_value = str(tmp_path / "out")
    return PandasCleaningEngine(repo, storage), project_id, dataset_id


def test_target_encoding_rejects_non_numeric_target(tmp_path: Path) -> None:
    engine, project_id, dataset_id = _make_engine_with_csv(
        tmp_path,
        pd.DataFrame({"cat": ["x", "y"], "label": ["A", "B"]}),
    )
    body = CleanEncodeRequest(columns=["cat"], method="target_encoding", target_column="label")

    with pytest.raises(AppError) as exc:
        with patch.object(engine, "_persist_cleaned", return_value=MagicMock()):
            engine.encode(project_id, dataset_id, body)
    assert exc.value.code == ERR_DATASET_INVALID_PARAM
    assert "numeric" in exc.value.message.lower()
