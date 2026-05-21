"""CSV/JSON parsing — implements DataParserProtocol (pandas)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.errors import ERR_DATASET_INVALID_PARAM, AppError
from shared.protocols import ColumnMeta, DatasetFormat, ValidationResult


def column_meta_to_dict(meta: ColumnMeta) -> dict[str, Any]:
    return {
        "name": meta.name,
        "dtype": meta.dtype,
        "nullable": meta.nullable,
        "unique_count": meta.unique_count,
        "sample_values": meta.sample_values,
    }


def columns_meta_to_db(columns: list[ColumnMeta]) -> list[dict[str, Any]]:
    return [column_meta_to_dict(c) for c in columns]


def _pandas_dtype_to_api(dtype: Any) -> str:
    name = str(dtype)
    if name.startswith("int"):
        return "int"
    if name.startswith("float"):
        return "float"
    if name == "bool":
        return "bool"
    if "datetime" in name:
        return "datetime"
    return "string"


def _cell_value(value: Any) -> Any:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _records_from_df(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in df.to_dict(orient="records"):
        rows.append({k: _cell_value(v) for k, v in record.items()})
    return rows


class PandasDataParser:
    """Tabular file parser for upload complete and preview."""

    def detect_format(self, file_path: str) -> DatasetFormat:
        ext = Path(file_path).suffix.lower()
        if ext in {".csv", ".tsv"}:
            return DatasetFormat.CSV
        if ext in {".json", ".jsonl", ".ndjson"}:
            return DatasetFormat.JSON
        if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}:
            return DatasetFormat.IMAGE
        return DatasetFormat.OTHER

    def _read_df(self, file_path: str, format: DatasetFormat, *, nrows: int | None = None) -> pd.DataFrame:
        path = Path(file_path)
        if not path.is_file():
            raise AppError.not_found(f"Dataset file not found: {file_path}")

        if format == DatasetFormat.CSV:
            sep = "\t" if path.suffix.lower() == ".tsv" else ","
            return pd.read_csv(path, sep=sep, nrows=nrows)

        if format == DatasetFormat.JSON:
            if path.suffix.lower() in {".jsonl", ".ndjson"}:
                return pd.read_json(path, lines=True, nrows=nrows)
            with path.open(encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, list):
                df = pd.DataFrame(payload)
            elif isinstance(payload, dict):
                df = pd.json_normalize(payload)
            else:
                raise AppError.bad_request("Unsupported JSON structure", code=ERR_DATASET_INVALID_PARAM)
            if nrows is not None:
                df = df.head(nrows)
            return df

        raise AppError.bad_request(
            f"Format {format.value} is not supported for tabular parsing",
            code=ERR_DATASET_INVALID_PARAM,
        )

    def load_dataframe(self, file_path: str, format: DatasetFormat) -> pd.DataFrame:
        """Load full tabular dataset into a DataFrame."""
        return self._read_df(file_path, format)

    def parse(
        self,
        file_path: str,
        format: DatasetFormat,
        *,
        limit: int | None = None,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        df = self._read_df(file_path, format, nrows=limit)
        columns = [str(c) for c in df.columns.tolist()]
        return columns, _records_from_df(df)

    def get_columns_meta(self, file_path: str, format: DatasetFormat) -> list[ColumnMeta]:
        df = self._read_df(file_path, format)
        metas: list[ColumnMeta] = []
        for col in df.columns:
            series = df[col]
            samples = [
                _cell_value(v)
                for v in series.dropna().head(20).tolist()
                if _cell_value(v) is not None
            ][:3]
            metas.append(
                ColumnMeta(
                    name=str(col),
                    dtype=_pandas_dtype_to_api(series.dtype),
                    nullable=bool(series.isnull().any()),
                    unique_count=int(series.nunique(dropna=True)),
                    sample_values=samples,
                )
            )
        return metas

    def count_rows(self, file_path: str, format: DatasetFormat) -> int:
        if format == DatasetFormat.CSV:
            path = Path(file_path)
            sep = "\t" if path.suffix.lower() == ".tsv" else ","
            # Fast row count without loading full frame into memory
            with path.open(encoding="utf-8", errors="replace") as f:
                line_count = sum(1 for _ in f)
            return max(0, line_count - 1)
        return len(self._read_df(file_path, format))

    def validate_file(self, file_path: str, format: DatasetFormat) -> ValidationResult:
        path = Path(file_path)
        errors: list[dict[str, str]] = []
        warnings: list[dict[str, str]] = []

        if not path.is_file():
            errors.append({"field": "file_path", "message": "File does not exist"})
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        if format in (DatasetFormat.CSV, DatasetFormat.JSON):
            try:
                self._read_df(file_path, format, nrows=5)
            except AppError:
                raise
            except Exception as exc:
                errors.append({"field": "file", "message": str(exc)})

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
