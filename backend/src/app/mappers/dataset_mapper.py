from __future__ import annotations

from pathlib import Path
from typing import Any

from app.db.models import DatasetRow
from app.schemas.dataset import ColumnMetaSchema, DatasetSchema


def _normalize_columns_meta(raw: list | dict | None) -> list[ColumnMetaSchema]:
    if not raw:
        return []
    if isinstance(raw, dict):
        return [
            ColumnMetaSchema(name=k, dtype=v.get("dtype", "object"), nullable=bool(v.get("nullable", True)))
            for k, v in raw.items()
        ]
    result: list[ColumnMetaSchema] = []
    for item in raw:
        if isinstance(item, ColumnMetaSchema):
            result.append(item)
        elif isinstance(item, dict) and "name" in item:
            result.append(ColumnMetaSchema(**item))
    return result


def row_to_dataset_schema(row: DatasetRow, *, size_bytes: int | None = None) -> DatasetSchema:
    columns = _normalize_columns_meta(row.columns_meta)
    return DatasetSchema(
        id=row.id,
        project_id=row.project_id,
        name=row.name,
        format=row.format,  # type: ignore[arg-type]
        file_path=row.file_path,
        num_samples=row.num_samples,
        num_columns=len(columns),
        columns_meta=columns,
        tags=list(row.tags or []),
        status=row.status,  # type: ignore[arg-type]
        size_bytes=size_bytes,
        created_at=row.created_at,
        updated_at=row.created_at,
    )


def file_size_if_exists(file_path: str) -> int | None:
    path = Path(file_path)
    return path.stat().st_size if path.is_file() else None
