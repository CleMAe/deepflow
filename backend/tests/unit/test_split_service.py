"""Unit tests for dataset split service."""

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from app.core.errors import ERR_DATASET_INVALID_PARAM, ERR_DATASET_NOT_FOUND, AppError
from app.schemas.eda import SplitRatios, SplitRequest
from app.services.split_service import (
    PandasSplitService,
    _normalize_ratios,
    _split_dataframe,
)


def test_normalize_ratios_rejects_invalid_sum() -> None:
    with pytest.raises(AppError) as exc:
        _normalize_ratios(0.5, 0.3, 0.3)
    assert exc.value.code == ERR_DATASET_INVALID_PARAM


def test_split_dataframe_stratified_preserves_row_count() -> None:
    df = pd.DataFrame({"label": ["A"] * 4 + ["B"] * 6, "v": range(10)})
    train, val, test = _split_dataframe(df, 0.6, 0.2, 0.2, stratify_column="label", random_seed=1)
    assert len(train) + len(val) + len(test) == 10


def test_require_source_not_found_uses_dataset_error_code() -> None:
    repo = MagicMock()
    repo.get_by_id_and_project.return_value = None
    svc = PandasSplitService(repo, MagicMock())
    with pytest.raises(AppError) as exc:
        svc._require_source(uuid.uuid4(), uuid.uuid4())
    assert exc.value.code == ERR_DATASET_NOT_FOUND


def test_split_writes_files_and_db_records(tmp_path: Path) -> None:
    project_id = uuid.uuid4()
    source_id = uuid.uuid4()
    csv_path = tmp_path / "source.csv"
    pd.DataFrame({"x": range(10), "y": ["a", "b"] * 5}).to_csv(csv_path, index=False)

    row = MagicMock()
    row.id = source_id
    row.name = "src"
    row.file_path = str(csv_path)
    row.format = MagicMock(value="csv")
    row.tags = []

    repo = MagicMock()
    repo.get_by_id_and_project.return_value = row

    created_rows: list[MagicMock] = []

    def _create(**kwargs):
        m = MagicMock()
        m.id = kwargs["dataset_id"]
        created_rows.append(m)
        return m

    repo.create.side_effect = _create

    storage = MagicMock()
    storage.get_raw_path.side_effect = lambda pid, did: str(tmp_path / "raw" / pid / did)

    svc = PandasSplitService(repo, storage)
    result = svc.split(
        project_id,
        source_id,
        SplitRequest(ratios=SplitRatios(train=0.6, val=0.2, test=0.2), random_seed=42),
    )

    assert result.train_count + result.val_count + result.test_count == 10
    assert result.train_dataset_id is not None
    assert len(created_rows) == 3
    train_path = Path(storage.get_raw_path(str(project_id), str(result.train_dataset_id))) / "train.csv"
    assert train_path.is_file()
