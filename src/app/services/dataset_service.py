from __future__ import annotations

import uuid

from app.core.errors import AppError
from src.infra.db.models import Dataset
from app.mappers.dataset_mapper import file_size_if_exists, row_to_dataset_schema
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.dataset import (
    BatchLabelUpdate,
    DatasetCreate,
    DatasetPreviewSchema,
    DatasetSchema,
    DatasetUpdate,
    PaginatedDatasets,
    PaginatedImages,
)
from shared.protocols import StorageProtocol


class DatasetService:
    def __init__(self, repo: DatasetRepository, storage: StorageProtocol) -> None:
        self._repo = repo
        self._storage = storage

    def _require_row(self, project_id: uuid.UUID, dataset_id: uuid.UUID) -> Dataset:
        row = self._repo.get_by_id_and_project(dataset_id, project_id)
        if not row:
            raise AppError.not_found(
                "Dataset not found",
                data={"dataset_id": str(dataset_id), "project_id": str(project_id)},
            )
        return row

    def list_datasets(
        self,
        project_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
        format_filter: str | None = None,
        status_filter: str | None = None,
        search: str | None = None,
    ) -> PaginatedDatasets:
        rows, total = self._repo.list_by_project(
            project_id,
            page=page,
            page_size=page_size,
            format_filter=format_filter,
            status_filter=status_filter,
            search=search,
        )
        items = [row_to_dataset_schema(r, size_bytes=file_size_if_exists(r.file_path or "")) for r in rows]
        return PaginatedDatasets(page=page, page_size=page_size, total=total, items=items)

    def create(self, project_id: uuid.UUID, body: DatasetCreate) -> DatasetSchema:
        ds_id = uuid.uuid4()
        raw_path = self._storage.get_raw_path(str(project_id), str(ds_id))
        row = self._repo.create(
            project_id=project_id,
            name=body.name,
            format=body.format,
            file_path=raw_path,
            tags=body.tags,
            status="uploading",
        )
        return row_to_dataset_schema(row)

    def get(self, project_id: uuid.UUID, dataset_id: uuid.UUID) -> DatasetSchema:
        row = self._require_row(project_id, dataset_id)
        return row_to_dataset_schema(row, size_bytes=file_size_if_exists(row.file_path or ""))

    def update(self, project_id: uuid.UUID, dataset_id: uuid.UUID, body: DatasetUpdate) -> DatasetSchema:
        row = self._require_row(project_id, dataset_id)
        row = self._repo.update(row, name=body.name, tags=body.tags)
        return row_to_dataset_schema(row)

    def delete(self, project_id: uuid.UUID, dataset_id: uuid.UUID) -> None:
        row = self._require_row(project_id, dataset_id)
        self._repo.delete(row)

    def preview(self, project_id: uuid.UUID, dataset_id: uuid.UUID, limit: int = 100) -> DatasetPreviewSchema:
        row = self._require_row(project_id, dataset_id)
        columns = ["col_a", "col_b"]
        rows = [{"col_a": 1, "col_b": 2}]
        if row.columns_meta:
            from app.mappers.dataset_mapper import _normalize_columns_meta

            cols = _normalize_columns_meta(row.columns_meta)
            if cols:
                columns = [c.name for c in cols]
        return DatasetPreviewSchema(columns=columns, rows=rows[:limit], total_rows=row.num_samples or len(rows), limit=limit)

    def list_images(self, project_id: uuid.UUID, dataset_id: uuid.UUID, page: int, page_size: int) -> PaginatedImages:
        self._require_row(project_id, dataset_id)
        from uuid import uuid4

        from app.schemas.dataset import ImageItemSchema

        items = [
            ImageItemSchema(
                id=uuid4(),
                filename=f"sample_{i:03d}.jpg",
                thumbnail_path=f"/projects/{project_id}/datasets/{dataset_id}/thumbs/sample_{i:03d}.jpg",
                labels=["cat"] if i % 2 == 0 else ["dog"],
                width=224,
                height=224,
            )
            for i in range((page - 1) * page_size + 1, (page - 1) * page_size + page_size + 1)
        ]
        return PaginatedImages(page=page, page_size=page_size, total=200, items=items)

    def update_labels(self, project_id: uuid.UUID, dataset_id: uuid.UUID, body: BatchLabelUpdate) -> dict:
        self._require_row(project_id, dataset_id)
        return {"updated": len(body.items)}
