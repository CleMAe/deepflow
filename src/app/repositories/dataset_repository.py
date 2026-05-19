"""Data access via SQLAlchemy ORM only — no raw SQL string concatenation."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import DatasetRow

_UPDATABLE_FIELDS = frozenset({"name", "format", "file_path", "num_samples", "columns_meta", "tags", "status"})


def _escape_like_pattern(value: str) -> str:
    """Escape SQL LIKE wildcards in user-provided search text."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class DatasetRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, dataset_id: uuid.UUID) -> DatasetRow | None:
        return self._db.get(DatasetRow, dataset_id)

    def get_by_id_and_project(self, dataset_id: uuid.UUID, project_id: uuid.UUID) -> DatasetRow | None:
        stmt = select(DatasetRow).where(
            DatasetRow.id == dataset_id,
            DatasetRow.project_id == project_id,
        )
        return self._db.scalar(stmt)

    def list_by_project(
        self,
        project_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
        format_filter: str | None = None,
        status_filter: str | None = None,
        search: str | None = None,
    ) -> tuple[list[DatasetRow], int]:
        filters = [DatasetRow.project_id == project_id]
        if format_filter:
            filters.append(DatasetRow.format == format_filter)
        if status_filter:
            filters.append(DatasetRow.status == status_filter)
        if search:
            escaped = _escape_like_pattern(search)
            filters.append(DatasetRow.name.ilike(f"%{escaped}%", escape="\\"))

        count_stmt = select(func.count()).select_from(DatasetRow).where(*filters)
        total = int(self._db.scalar(count_stmt) or 0)

        stmt = (
            select(DatasetRow)
            .where(*filters)
            .order_by(DatasetRow.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self._db.scalars(stmt).all())
        return items, total

    def create(
        self,
        *,
        dataset_id: uuid.UUID | None = None,
        project_id: uuid.UUID,
        name: str,
        format: str,
        file_path: str,
        num_samples: int = 0,
        columns_meta: list | dict | None = None,
        tags: list[str] | None = None,
        status: str = "uploading",
    ) -> DatasetRow:
        row = DatasetRow(
            id=dataset_id or uuid.uuid4(),
            project_id=project_id,
            name=name,
            format=format,
            file_path=file_path,
            num_samples=num_samples,
            columns_meta=columns_meta or [],
            tags=tags or [],
            status=status,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def update(self, row: DatasetRow, **fields) -> DatasetRow:
        for key, value in fields.items():
            if key not in _UPDATABLE_FIELDS:
                continue
            if value is not None:
                setattr(row, key, value)
        self._db.commit()
        self._db.refresh(row)
        return row

    def delete(self, row: DatasetRow) -> None:
        self._db.delete(row)
        self._db.commit()
