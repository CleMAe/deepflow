"""Dataset train/val/test split — writes real files and DB records."""

from __future__ import annotations

import uuid
from pathlib import Path

import numpy as np
import pandas as pd

from app.core.errors import AppError, ERR_DATASET_INVALID_PARAM, ERR_DATASET_NOT_FOUND
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.eda import SplitRequest, SplitResultSchema
from app.services.data_parser import PandasDataParser, columns_meta_to_db
from shared.protocols import DataParserProtocol, DatasetFormat, StorageProtocol


def _normalize_ratios(train: float, val: float | None, test: float | None) -> tuple[float, float, float]:
    val_r = val or 0.0
    test_r = test if test is not None else max(0.0, 1.0 - train - val_r)
    total = train + val_r + test_r
    if total <= 0 or abs(total - 1.0) > 0.02:
        raise AppError.bad_request(
            "Split ratios must sum to 1.0",
            code=ERR_DATASET_INVALID_PARAM,
            data={"train": train, "val": val_r, "test": test_r, "sum": total},
        )
    return train, val_r, test_r


def _partition_indices(
    n: int,
    train_r: float,
    val_r: float,
    test_r: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if n == 0:
        return np.array([], dtype=int), np.array([], dtype=int), np.array([], dtype=int)
    perm = rng.permutation(n)
    train_n = int(n * train_r)
    val_n = int(n * val_r)
    test_n = n - train_n - val_n
    if test_n < 0:
        test_n = 0
        val_n = n - train_n
    return perm[:train_n], perm[train_n : train_n + val_n], perm[train_n + val_n :]


def _split_dataframe(
    df: pd.DataFrame,
    train_r: float,
    val_r: float,
    test_r: float,
    *,
    stratify_column: str | None,
    random_seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(random_seed)
    if stratify_column and stratify_column in df.columns:
        train_parts: list[pd.DataFrame] = []
        val_parts: list[pd.DataFrame] = []
        test_parts: list[pd.DataFrame] = []
        for _, group in df.groupby(stratify_column, dropna=False):
            idx = group.index.to_numpy()
            n = len(idx)
            t_i, v_i, s_i = _partition_indices(n, train_r, val_r, test_r, rng)
            train_parts.append(df.loc[idx[t_i]])
            val_parts.append(df.loc[idx[v_i]])
            test_parts.append(df.loc[idx[s_i]])
        train_df = pd.concat(train_parts, ignore_index=True) if train_parts else df.iloc[0:0]
        val_df = pd.concat(val_parts, ignore_index=True) if val_parts else df.iloc[0:0]
        test_df = pd.concat(test_parts, ignore_index=True) if test_parts else df.iloc[0:0]
        return train_df, val_df, test_df

    n = len(df)
    t_i, v_i, s_i = _partition_indices(n, train_r, val_r, test_r, rng)
    return df.iloc[t_i], df.iloc[v_i], df.iloc[s_i]


class PandasSplitService:
    def __init__(
        self,
        repo: DatasetRepository,
        storage: StorageProtocol,
        parser: DataParserProtocol | None = None,
    ) -> None:
        self._repo = repo
        self._storage = storage
        self._parser = parser or PandasDataParser()

    def _require_source(self, project_id: uuid.UUID, dataset_id: uuid.UUID):
        row = self._repo.get_by_id_and_project(dataset_id, project_id)
        if not row:
            raise AppError.not_found("Dataset not found", code=ERR_DATASET_NOT_FOUND)
        fmt_value = row.format.value if hasattr(row.format, "value") else str(row.format)
        if fmt_value not in ("csv", "json"):
            raise AppError.bad_request(
                "Split is only supported for csv/json datasets",
                code=ERR_DATASET_INVALID_PARAM,
            )
        path = row.file_path or ""
        if not path or not Path(path).is_file():
            raise AppError.bad_request("Dataset file is missing", code=ERR_DATASET_INVALID_PARAM)
        return row, DatasetFormat(fmt_value)

    def _persist_part(
        self,
        project_id: uuid.UUID,
        source,
        part_df: pd.DataFrame,
        part_name: str,
        fmt: DatasetFormat,
    ):
        if part_df.empty:
            return None

        new_id = uuid.uuid4()
        raw_dir = Path(self._storage.get_raw_path(str(project_id), str(new_id)))
        raw_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(source.file_path or "").suffix.lower() or ".csv"
        if ext not in {".csv", ".tsv", ".json", ".jsonl"}:
            ext = ".csv"
        out_path = raw_dir / f"{part_name}{ext}"
        if ext in {".json", ".jsonl"}:
            part_df.to_json(out_path, orient="records", lines=ext == ".jsonl", force_ascii=False)
        else:
            sep = "\t" if ext == ".tsv" else ","
            part_df.to_csv(out_path, index=False, sep=sep)

        columns_meta = self._parser.get_columns_meta(str(out_path), fmt)
        row = self._repo.create(
            dataset_id=new_id,
            project_id=project_id,
            name=f"{source.name}_{part_name}",
            format=fmt.value,
            file_path=str(out_path),
            num_samples=len(part_df),
            num_columns=len(columns_meta),
            columns_meta=columns_meta_to_db(columns_meta),
            tags=list(source.tags or []) + ["split", part_name],
            status="ready",
        )
        return row

    def split(
        self,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        body: SplitRequest,
    ) -> SplitResultSchema:
        source, fmt = self._require_source(project_id, dataset_id)
        train_r, val_r, test_r = _normalize_ratios(
            body.ratios.train,
            body.ratios.val,
            body.ratios.test,
        )

        df = self._parser.load_dataframe(source.file_path, fmt)  # type: ignore[union-attr]
        if body.stratify_column and body.stratify_column not in df.columns:
            raise AppError.bad_request(
                f"Stratify column not found: {body.stratify_column}",
                code=ERR_DATASET_INVALID_PARAM,
            )

        train_df, val_df, test_df = _split_dataframe(
            df,
            train_r,
            val_r,
            test_r,
            stratify_column=body.stratify_column,
            random_seed=body.random_seed,
        )

        train_row = self._persist_part(project_id, source, train_df, "train", fmt)
        val_row = self._persist_part(project_id, source, val_df, "val", fmt) if val_r > 0 else None
        test_row = self._persist_part(project_id, source, test_df, "test", fmt) if test_r > 0 else None

        if train_row is None:
            raise AppError.bad_request("Train split is empty", code=ERR_DATASET_INVALID_PARAM)

        return SplitResultSchema(
            train_dataset_id=train_row.id,
            val_dataset_id=val_row.id if val_row else None,
            test_dataset_id=test_row.id if test_row else None,
            train_count=len(train_df),
            val_count=len(val_df),
            test_count=len(test_df),
        )
