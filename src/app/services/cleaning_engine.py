"""Pandas cleaning engine — implements cleaning operations for tabular datasets."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.errors import AppError, ERR_DATASET_INVALID_PARAM
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.cleaning import (
    CleanDedupRequest,
    CleanEncodeRequest,
    CleanMissingRequest,
    CleanOutlierRequest,
    CleanTypeConvertRequest,
    CleaningResultSchema,
)
from app.services.data_parser import PandasDataParser, columns_meta_to_db
from shared.protocols import DataParserProtocol, DatasetFormat, StorageProtocol


class PandasCleaningEngine:
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
            raise AppError.not_found("Dataset not found")
        fmt = row.format.value if hasattr(row.format, "value") else str(row.format)
        if fmt not in ("csv", "json"):
            raise AppError.bad_request(
                "Cleaning is only supported for csv/json datasets",
                code=ERR_DATASET_INVALID_PARAM,
            )
        if not row.file_path or not Path(row.file_path).is_file():
            raise AppError.bad_request("Dataset file is missing", code=ERR_DATASET_INVALID_PARAM)
        return row, DatasetFormat(fmt)

    def _load_df(self, file_path: str, fmt: DatasetFormat) -> pd.DataFrame:
        parser = self._parser
        if not hasattr(parser, "load_dataframe"):
            raise AppError.bad_request("Parser does not support load_dataframe", code=ERR_DATASET_INVALID_PARAM)
        return parser.load_dataframe(file_path, fmt)  # type: ignore[union-attr]

    def _persist_cleaned(
        self,
        project_id: uuid.UUID,
        source,
        df: pd.DataFrame,
        operation: str,
        fmt: DatasetFormat,
        changes_summary: dict[str, Any],
        columns_affected: list[str],
        rows_before: int,
    ) -> CleaningResultSchema:
        new_id = uuid.uuid4()
        cleaned_dir = Path(self._storage.get_cleaned_path(str(project_id), str(new_id)))
        cleaned_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(source.file_path or "").suffix.lower() or ".csv"
        if ext not in {".csv", ".tsv", ".json", ".jsonl"}:
            ext = ".csv"
        out_path = cleaned_dir / f"cleaned{ext}"
        if ext in {".json", ".jsonl"}:
            df.to_json(out_path, orient="records", lines=ext == ".jsonl", force_ascii=False)
        else:
            sep = "\t" if ext == ".tsv" else ","
            df.to_csv(out_path, index=False, sep=sep)

        columns_meta = self._parser.get_columns_meta(str(out_path), fmt)
        num_samples = len(df)
        source_name = source.name
        row = self._repo.create(
            dataset_id=new_id,
            project_id=project_id,
            name=f"{source_name}_{operation}",
            format=fmt.value,
            file_path=str(out_path),
            num_samples=num_samples,
            num_columns=len(columns_meta),
            columns_meta=columns_meta_to_db(columns_meta),
            tags=list(source.tags or []),
            status="cleaned",
        )
        return CleaningResultSchema(
            rows_before=rows_before,
            rows_after=num_samples,
            columns_affected=columns_affected,
            changes_summary=changes_summary,
            dataset_id=row.id,
        )

    def handle_missing(
        self,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        body: CleanMissingRequest,
    ) -> CleaningResultSchema:
        source, fmt = self._require_source(project_id, dataset_id)
        df = self._load_df(source.file_path, fmt)
        rows_before = len(df)
        target_cols = body.columns or df.columns.tolist()
        columns_affected = [c for c in target_cols if c in df.columns]
        if not columns_affected:
            raise AppError.bad_request("No valid columns to clean", code=ERR_DATASET_INVALID_PARAM)

        strategy = body.strategy
        if strategy == "drop_row":
            df = df.dropna(subset=columns_affected)
        elif strategy == "fill_mean":
            for col in columns_affected:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].mean())
        elif strategy == "fill_median":
            for col in columns_affected:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
        elif strategy == "fill_mode":
            for col in columns_affected:
                mode = df[col].mode(dropna=True)
                if len(mode):
                    df[col] = df[col].fillna(mode.iloc[0])
        elif strategy == "fill_constant":
            for col in columns_affected:
                df[col] = df[col].fillna(body.fill_value)
        elif strategy == "forward_fill":
            df[columns_affected] = df[columns_affected].ffill()
        elif strategy == "backward_fill":
            df[columns_affected] = df[columns_affected].bfill()
        else:
            raise AppError.bad_request(f"Unknown strategy: {strategy}", code=ERR_DATASET_INVALID_PARAM)

        return self._persist_cleaned(
            project_id,
            source,
            df,
            "missing",
            fmt,
            {"operation": "missing", "strategy": strategy, "columns": columns_affected},
            columns_affected,
            rows_before,
        )

    def detect_outliers(
        self,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        body: CleanOutlierRequest,
    ) -> CleaningResultSchema:
        source, fmt = self._require_source(project_id, dataset_id)
        df = self._load_df(source.file_path, fmt)
        rows_before = len(df)
        columns_affected = [c for c in body.columns if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
        if not columns_affected:
            raise AppError.bad_request("No numeric columns for outlier detection", code=ERR_DATASET_INVALID_PARAM)

        threshold = body.threshold if body.threshold is not None else 3.0
        mask = pd.Series(False, index=df.index)
        for col in columns_affected:
            series = df[col]
            if body.method == "zscore":
                std = series.std()
                if std == 0 or pd.isna(std):
                    continue
                z = (series - series.mean()) / std
                col_mask = z.abs() > threshold
            elif body.method == "iqr":
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - threshold * iqr
                upper = q3 + threshold * iqr
                col_mask = (series < lower) | (series > upper)
            else:
                raise AppError.bad_request(f"Unknown method: {body.method}", code=ERR_DATASET_INVALID_PARAM)
            mask = mask | col_mask.fillna(False)

        if body.action == "drop":
            df = df.loc[~mask]
        elif body.action == "clip":
            for col in columns_affected:
                series = df[col]
                if body.method == "iqr":
                    q1, q3 = series.quantile(0.25), series.quantile(0.75)
                    iqr = q3 - q1
                    lower, upper = q1 - threshold * iqr, q3 + threshold * iqr
                else:
                    std = series.std() or 1
                    lower, upper = series.mean() - threshold * std, series.mean() + threshold * std
                df[col] = series.clip(lower=lower, upper=upper)
        elif body.action == "mark":
            df["_outlier_flag"] = mask
            columns_affected = columns_affected + ["_outlier_flag"]
        else:
            raise AppError.bad_request(f"Unknown action: {body.action}", code=ERR_DATASET_INVALID_PARAM)

        return self._persist_cleaned(
            project_id,
            source,
            df,
            "outlier",
            fmt,
            {
                "operation": "outlier",
                "method": body.method,
                "action": body.action,
                "threshold": threshold,
                "outliers_found": int(mask.sum()),
            },
            columns_affected,
            rows_before,
        )

    def deduplicate(
        self,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        body: CleanDedupRequest,
    ) -> CleaningResultSchema:
        source, fmt = self._require_source(project_id, dataset_id)
        df = self._load_df(source.file_path, fmt)
        rows_before = len(df)
        subset = body.columns or None
        columns_affected = list(subset) if subset else list(df.columns.astype(str))
        keep = body.keep if body.keep in ("first", "last") else "first"
        if body.keep == "none":
            df = df.drop_duplicates(subset=subset, keep=False)
        else:
            df = df.drop_duplicates(subset=subset, keep=keep)

        removed = rows_before - len(df)
        return self._persist_cleaned(
            project_id,
            source,
            df,
            "dedup",
            fmt,
            {"operation": "dedup", "keep": body.keep, "duplicates_removed": removed},
            columns_affected,
            rows_before,
        )

    def encode(
        self,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        body: CleanEncodeRequest,
    ) -> CleaningResultSchema:
        source, fmt = self._require_source(project_id, dataset_id)
        df = self._load_df(source.file_path, fmt)
        rows_before = len(df)
        columns_affected = [c for c in body.columns if c in df.columns]
        if not columns_affected:
            raise AppError.bad_request("No valid columns to encode", code=ERR_DATASET_INVALID_PARAM)

        if body.method == "label_encoding":
            for col in columns_affected:
                df[col] = pd.Categorical(df[col]).codes
        elif body.method == "one_hot":
            df = pd.get_dummies(df, columns=columns_affected, prefix=columns_affected, dtype=int)
            columns_affected = [c for c in df.columns if any(c.startswith(f"{x}_") for x in body.columns)]
        else:
            raise AppError.bad_request(f"Unsupported encode method: {body.method}", code=ERR_DATASET_INVALID_PARAM)

        return self._persist_cleaned(
            project_id,
            source,
            df,
            "encode",
            fmt,
            {"operation": "encode", "method": body.method},
            columns_affected,
            rows_before,
        )

    def type_convert(
        self,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        body: CleanTypeConvertRequest,
    ) -> CleaningResultSchema:
        source, fmt = self._require_source(project_id, dataset_id)
        df = self._load_df(source.file_path, fmt)
        rows_before = len(df)
        columns_affected: list[str] = []
        for item in body.conversions:
            if item.column not in df.columns:
                continue
            columns_affected.append(item.column)
            if item.target_type == "int":
                df[item.column] = pd.to_numeric(df[item.column], errors="coerce").astype("Int64")
            elif item.target_type == "float":
                df[item.column] = pd.to_numeric(df[item.column], errors="coerce")
            elif item.target_type == "str":
                df[item.column] = df[item.column].astype(str)
            elif item.target_type == "bool":
                df[item.column] = df[item.column].astype(bool)
            elif item.target_type == "datetime":
                df[item.column] = pd.to_datetime(df[item.column], format=item.datetime_format, errors="coerce")
            else:
                raise AppError.bad_request(
                    f"Unsupported target_type: {item.target_type}",
                    code=ERR_DATASET_INVALID_PARAM,
                )

        return self._persist_cleaned(
            project_id,
            source,
            df,
            "type-convert",
            fmt,
            {"operation": "type-convert", "conversions": len(body.conversions)},
            columns_affected,
            rows_before,
        )
