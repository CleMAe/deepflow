from __future__ import annotations

import uuid

from app.core.errors import AppError
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
from app.services.data_parser import PandasDataParser
from shared.protocols import DataParserProtocol, DatasetFormat, StorageProtocol
from src.infra.db.models import Dataset


class DatasetService:
    def __init__(
        self,
        repo: DatasetRepository,
        storage: StorageProtocol,
        parser: DataParserProtocol | None = None,
    ) -> None:
        self._repo = repo
        self._storage = storage
        self._parser = parser or PandasDataParser()

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
        file_path = row.file_path or ""
        fmt_value = row.format.value if hasattr(row.format, "value") else str(row.format)

        if fmt_value not in ("csv", "json") or not file_path:
            from app.mappers.dataset_mapper import _normalize_columns_meta

            columns: list[str] = []
            if row.columns_meta:
                cols = _normalize_columns_meta(row.columns_meta)
                columns = [c.name for c in cols]
            return DatasetPreviewSchema(
                columns=columns,
                rows=[],
                total_rows=row.num_samples or 0,
                limit=limit,
            )

        ds_format = DatasetFormat(fmt_value)
        columns, rows = self._parser.parse(file_path, ds_format, limit=limit)
        total_rows = row.num_samples or self._parser.count_rows(file_path, ds_format)
        return DatasetPreviewSchema(columns=columns, rows=rows, total_rows=total_rows, limit=limit)

    def list_images(self, project_id: uuid.UUID, dataset_id: uuid.UUID, page: int, page_size: int) -> PaginatedImages:
        row = self._require_row(project_id, dataset_id)
        from app.schemas.dataset import ImageItemSchema
        from app.services.image_gallery import (
            iter_readable_images,
            load_labels_map,
            stable_image_id,
        )

        readable = iter_readable_images(row.file_path or "")
        total = len(readable)
        start = (page - 1) * page_size
        end = start + page_size
        labels_map = load_labels_map(row.file_path or "")
        items = []
        for path, w, h in readable[start:end]:
            filename = path.name
            items.append(
                ImageItemSchema(
                    id=stable_image_id(project_id, dataset_id, filename),
                    filename=filename,
                    thumbnail_path=f"/projects/{project_id}/datasets/{dataset_id}/thumbs/{filename}",
                    labels=labels_map.get(filename, []),
                    width=w,
                    height=h,
                )
            )
        return PaginatedImages(page=page, page_size=page_size, total=total, items=items)

    def update_labels(self, project_id: uuid.UUID, dataset_id: uuid.UUID, body: BatchLabelUpdate) -> dict:
        row = self._require_row(project_id, dataset_id)
        from app.services.image_gallery import load_labels_map, save_labels_map

        labels = load_labels_map(row.file_path or "")
        for item in body.items:
            labels[item.filename] = list(item.labels)
        save_labels_map(row.file_path or "", labels)
        return {"updated": len(body.items)}
