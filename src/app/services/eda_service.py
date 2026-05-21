"""EDA service — pandas statistics + ECharts-friendly visualization payloads."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from app.core.errors import ERR_DATASET_INVALID_PARAM, AppError
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.eda import EdaRequest
from app.services.data_parser import PandasDataParser
from shared.protocols import DataParserProtocol, DatasetFormat

# Module-level in-memory cache (shared across requests; lost on process restart).
# Day2/3 acceptable; persist to DB or meta.json in a later iteration.
_REPORT_CACHE: dict[str, dict[str, Any]] = {}


def _dtype_label(dtype: Any) -> str:
    name = str(dtype)
    if name.startswith("int") or name.startswith("float"):
        return "numeric"
    if "datetime" in name:
        return "datetime"
    if name == "bool":
        return "boolean"
    return "categorical"


class PandasEdaService:
    """EDA statistics; reports stored in module-level _REPORT_CACHE (survives per-request DI instances)."""

    def __init__(
        self,
        repo: DatasetRepository,
        parser: DataParserProtocol | None = None,
    ) -> None:
        self._repo = repo
        self._parser = parser or PandasDataParser()

    def _cache_key(self, project_id: uuid.UUID, dataset_id: uuid.UUID) -> str:
        return f"{project_id}:{dataset_id}"

    def _load_dataset(self, project_id: uuid.UUID, dataset_id: uuid.UUID):
        row = self._repo.get_by_id_and_project(dataset_id, project_id)
        if not row:
            raise AppError.not_found("Dataset not found")
        fmt_value = row.format.value if hasattr(row.format, "value") else str(row.format)
        if fmt_value not in ("csv", "json"):
            raise AppError.bad_request(
                "EDA is only supported for csv/json datasets",
                code=ERR_DATASET_INVALID_PARAM,
            )
        if not row.file_path:
            raise AppError.bad_request("Dataset file is missing", code=ERR_DATASET_INVALID_PARAM)
        return row, DatasetFormat(fmt_value)

    def _build_report(
        self,
        dataset_id: uuid.UUID,
        df: pd.DataFrame,
        *,
        columns: list[str] | None,
        include_visualizations: bool,
    ) -> dict[str, Any]:
        if columns:
            selected = [c for c in columns if c in df.columns]
            if not selected:
                raise AppError.bad_request("No valid columns for EDA", code=ERR_DATASET_INVALID_PARAM)
            df = df[selected]

        num_rows = len(df)
        num_columns = len(df.columns)
        num_missing = int(df.isnull().sum().sum())
        duplicate_rows = int(df.duplicated().sum())

        column_stats: list[dict[str, Any]] = []
        numeric_cols: list[str] = []

        for col in df.columns:
            series = df[col]
            missing_count = int(series.isnull().sum())
            stat: dict[str, Any] = {
                "name": str(col),
                "dtype": _dtype_label(series.dtype),
                "missing_count": missing_count,
                "missing_pct": round(missing_count / num_rows * 100, 2) if num_rows else 0.0,
                "unique_count": int(series.nunique(dropna=True)),
            }
            if pd.api.types.is_numeric_dtype(series):
                numeric_cols.append(str(col))
                desc = series.describe()
                for key in ("mean", "std", "min", "25%", "50%", "75%", "max"):
                    val = desc.get(key)
                    if val is not None and not pd.isna(val):
                        api_key = "q25" if key == "25%" else "median" if key == "50%" else "q75" if key == "75%" else key
                        stat[api_key] = float(val)
            else:
                top = series.value_counts(dropna=True).head(5)
                stat["top_values"] = [
                    {"value": v if not hasattr(v, "item") else v.item(), "count": int(c)}
                    for v, c in top.items()
                ]
            column_stats.append(stat)

        correlations: dict[str, dict[str, float]] = {}
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr(numeric_only=True)
            for row_name in corr.index:
                correlations[str(row_name)] = {
                    str(col_name): float(corr.loc[row_name, col_name])
                    for col_name in corr.columns
                    if not pd.isna(corr.loc[row_name, col_name])
                }

        visualizations: list[dict[str, Any]] = []
        if include_visualizations:
            for col in numeric_cols[:5]:
                counts, bins = pd.cut(df[col].dropna(), bins=10, retbins=True)
                hist = counts.value_counts().sort_index()
                visualizations.append(
                    {
                        "type": "histogram",
                        "title": f"{col} distribution",
                        "config": {
                            "xAxis": {"type": "category", "data": [str(i) for i in range(len(hist))]},
                            "yAxis": {"type": "value"},
                            "series": [{"type": "bar", "data": [int(v) for v in hist.values]}],
                        },
                    }
                )
                visualizations.append(
                    {
                        "type": "boxplot",
                        "title": f"{col} boxplot",
                        "config": {
                            "xAxis": {"type": "category", "data": [col]},
                            "yAxis": {"type": "value"},
                            "series": [
                                {
                                    "type": "boxplot",
                                    "data": [[float(df[col].min()), float(df[col].quantile(0.25)), float(df[col].median()), float(df[col].quantile(0.75)), float(df[col].max())]],
                                }
                            ],
                        },
                    }
                )
            if len(numeric_cols) >= 2:
                visualizations.append(
                    {
                        "type": "heatmap",
                        "title": "Correlation heatmap",
                        "config": {
                            "xAxis": {"type": "category", "data": numeric_cols},
                            "yAxis": {"type": "category", "data": numeric_cols},
                            "series": [
                                {
                                    "type": "heatmap",
                                    "data": [
                                        [i, j, correlations.get(numeric_cols[i], {}).get(numeric_cols[j], 0)]
                                        for i in range(len(numeric_cols))
                                        for j in range(len(numeric_cols))
                                    ],
                                }
                            ],
                        },
                    }
                )
            for col in [c for c in df.columns if c not in numeric_cols][:3]:
                top = df[col].value_counts(dropna=True).head(8)
                visualizations.append(
                    {
                        "type": "bar",
                        "title": f"{col} top values",
                        "config": {
                            "xAxis": {"type": "category", "data": [str(v) for v in top.index]},
                            "yAxis": {"type": "value"},
                            "series": [{"type": "bar", "data": [int(v) for v in top.values]}],
                        },
                    }
                )

        return {
            "dataset_id": str(dataset_id),
            "summary": {
                "num_rows": num_rows,
                "num_columns": num_columns,
                "num_missing": num_missing,
                "duplicate_rows": duplicate_rows,
            },
            "column_stats": column_stats,
            "correlations": correlations,
            "visualizations": visualizations,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def run_eda(self, project_id: uuid.UUID, dataset_id: uuid.UUID, body: EdaRequest) -> dict[str, Any]:
        row, fmt = self._load_dataset(project_id, dataset_id)
        df = self._parser.load_dataframe(row.file_path, fmt)  # type: ignore[union-attr]
        report = self._build_report(
            dataset_id,
            df,
            columns=body.columns or None,
            include_visualizations=body.include_visualizations,
        )
        _REPORT_CACHE[self._cache_key(project_id, dataset_id)] = report
        return report

    def get_report(self, project_id: uuid.UUID, dataset_id: uuid.UUID) -> dict[str, Any]:
        key = self._cache_key(project_id, dataset_id)
        report = _REPORT_CACHE.get(key)
        if not report:
            raise AppError.not_found("EDA report not found; run POST /eda first")
        return report
