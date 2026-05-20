from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.api.deps import (
    get_dataset_service,
    get_upload_service,
    require_project_access,
)
from app.core.response import success
from app.mappers.dataset_mapper import row_to_dataset_schema
from app.schemas.dataset import (
    BatchLabelUpdate,
    DatasetCreate,
    DatasetUpdate,
    UploadCompleteRequest,
    UploadInitRequest,
)
from app.services.dataset_service import DatasetService
from app.services.upload_service import UploadService

router = APIRouter(prefix="/projects/{project_id}/datasets", tags=["Datasets"])


@router.post("/upload", status_code=201)
async def simple_upload_dataset(
    project_id: UUID,
    file: UploadFile = File(...),
    name: str = Form(...),
    tags: str | None = Form(None),
    _: UUID = Depends(require_project_access),
    uploads: UploadService = Depends(get_upload_service),
):
    # V1.0: loads entire body into memory (limit enforced in UploadService, max 500MB).
    # Future: stream chunks to disk to avoid large in-memory buffers.
    data = await file.read()
    tag_list: list[str] = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    row = uploads.simple_upload(
        project_id,
        filename=file.filename or "upload.bin",
        data=data,
        name=name,
        tags=tag_list or None,
    )
    return success(row_to_dataset_schema(row).model_dump(mode="json"))


@router.post("/upload/init", dependencies=[])
async def init_upload(
    project_id: UUID,
    body: UploadInitRequest,
    _: UUID = Depends(require_project_access),
    uploads: UploadService = Depends(get_upload_service),
):
    session = uploads.init_upload(project_id, body)
    return success(session.model_dump(mode="json"))


@router.post("/upload/{upload_id}/chunk")
async def upload_chunk(
    project_id: UUID,
    upload_id: UUID,
    chunk: UploadFile = File(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    _: UUID = Depends(require_project_access),
    uploads: UploadService = Depends(get_upload_service),
):
    data = await chunk.read()
    session = uploads.save_chunk(upload_id, chunk_index, data)
    return success({"received_chunks": session.received_chunks})


@router.post("/upload/{upload_id}/complete")
async def complete_upload(
    project_id: UUID,
    upload_id: UUID,
    body: UploadCompleteRequest,
    _: UUID = Depends(require_project_access),
    uploads: UploadService = Depends(get_upload_service),
):
    row = uploads.complete(project_id, upload_id, body)
    return success(row_to_dataset_schema(row).model_dump(mode="json"))


@router.get("")
async def list_datasets(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    format: str | None = None,
    status: str | None = None,
    search: str | None = None,
    _: UUID = Depends(require_project_access),
    svc: DatasetService = Depends(get_dataset_service),
):
    payload = svc.list_datasets(
        project_id, page=page, page_size=page_size, format_filter=format, status_filter=status, search=search
    )
    return success(payload.model_dump(mode="json"))


@router.post("")
async def create_dataset(
    project_id: UUID,
    body: DatasetCreate,
    _: UUID = Depends(require_project_access),
    svc: DatasetService = Depends(get_dataset_service),
):
    ds = svc.create(project_id, body)
    return success(ds.model_dump(mode="json"))


@router.get("/{ds_id}")
async def get_dataset(
    project_id: UUID,
    ds_id: UUID,
    _: UUID = Depends(require_project_access),
    svc: DatasetService = Depends(get_dataset_service),
):
    return success(svc.get(project_id, ds_id).model_dump(mode="json"))


@router.put("/{ds_id}")
async def update_dataset(
    project_id: UUID,
    ds_id: UUID,
    body: DatasetUpdate,
    _: UUID = Depends(require_project_access),
    svc: DatasetService = Depends(get_dataset_service),
):
    return success(svc.update(project_id, ds_id, body).model_dump(mode="json"))


@router.delete("/{ds_id}")
async def delete_dataset(
    project_id: UUID,
    ds_id: UUID,
    _: UUID = Depends(require_project_access),
    svc: DatasetService = Depends(get_dataset_service),
):
    svc.delete(project_id, ds_id)
    return success({"dataset_id": str(ds_id)})


@router.get("/{ds_id}/preview")
async def preview_dataset(
    project_id: UUID,
    ds_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    _: UUID = Depends(require_project_access),
    svc: DatasetService = Depends(get_dataset_service),
):
    return success(svc.preview(project_id, ds_id, limit).model_dump(mode="json"))


@router.get("/{ds_id}/images")
async def list_images(
    project_id: UUID,
    ds_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    _: UUID = Depends(require_project_access),
    svc: DatasetService = Depends(get_dataset_service),
):
    return success(svc.list_images(project_id, ds_id, page, page_size).model_dump(mode="json"))


@router.put("/{ds_id}/labels")
async def update_labels(
    project_id: UUID,
    ds_id: UUID,
    body: BatchLabelUpdate,
    _: UUID = Depends(require_project_access),
    svc: DatasetService = Depends(get_dataset_service),
):
    return success(svc.update_labels(project_id, ds_id, body))
