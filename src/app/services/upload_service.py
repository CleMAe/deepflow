"""Chunked upload — file I/O only; metadata via DatasetRepository."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import settings
from app.core.errors import (
    ERR_DATASET_FORBIDDEN,
    ERR_UPLOAD_INCOMPLETE,
    ERR_UPLOAD_NOT_FOUND,
    AppError,
)
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.dataset import UploadCompleteRequest, UploadInitRequest, UploadSessionSchema
from shared.protocols import StorageProtocol


@dataclass
class _UploadState:
    upload_id: uuid.UUID
    project_id: uuid.UUID
    filename: str
    total_size: int
    total_chunks: int
    dataset_name: str | None
    format_hint: str | None
    chunk_size: int
    received_chunks: set[int] = field(default_factory=set)
    temp_dir: Path = field(default_factory=Path)


class UploadService:
    def __init__(self, storage: StorageProtocol, repo: DatasetRepository) -> None:
        self._storage = storage
        self._repo = repo
        self._sessions: dict[uuid.UUID, _UploadState] = {}
        self._meta_path = Path(settings.storage_root) / "uploads" / "_sessions.json"
        self._load_sessions()

    def _load_sessions(self) -> None:
        if self._meta_path.is_file():
            raw = json.loads(self._meta_path.read_text(encoding="utf-8"))
            for uid, data in raw.items():
                self._sessions[uuid.UUID(uid)] = _UploadState(
                    upload_id=uuid.UUID(uid),
                    project_id=uuid.UUID(data["project_id"]),
                    filename=data["filename"],
                    total_size=data["total_size"],
                    total_chunks=data["total_chunks"],
                    dataset_name=data.get("dataset_name"),
                    format_hint=data.get("format_hint"),
                    chunk_size=data["chunk_size"],
                    received_chunks=set(data.get("received_chunks", [])),
                    temp_dir=Path(data["temp_dir"]),
                )

    def _persist_sessions(self) -> None:
        self._meta_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            str(s.upload_id): {
                "project_id": str(s.project_id),
                "filename": s.filename,
                "total_size": s.total_size,
                "total_chunks": s.total_chunks,
                "dataset_name": s.dataset_name,
                "format_hint": s.format_hint,
                "chunk_size": s.chunk_size,
                "received_chunks": sorted(s.received_chunks),
                "temp_dir": str(s.temp_dir),
            }
            for s in self._sessions.values()
        }
        self._meta_path.write_text(json.dumps(payload), encoding="utf-8")

    def init_upload(self, project_id: uuid.UUID, body: UploadInitRequest) -> UploadSessionSchema:
        upload_id = uuid.uuid4()
        temp_dir = Path(self._storage.get_upload_temp_path())
        state = _UploadState(
            upload_id=upload_id,
            project_id=project_id,
            filename=body.filename,
            total_size=body.total_size,
            total_chunks=body.total_chunks,
            dataset_name=body.dataset_name,
            format_hint=body.format,
            chunk_size=settings.default_chunk_size,
            temp_dir=temp_dir,
        )
        self._sessions[upload_id] = state
        self._persist_sessions()
        return UploadSessionSchema(
            upload_id=upload_id,
            chunk_size=state.chunk_size,
            received_chunks=[],
        )

    def _get_session(self, upload_id: uuid.UUID) -> _UploadState:
        state = self._sessions.get(upload_id)
        if not state:
            raise AppError.not_found("Upload session not found", code=ERR_UPLOAD_NOT_FOUND)
        return state

    def save_chunk(self, upload_id: uuid.UUID, chunk_index: int, data: bytes) -> UploadSessionSchema:
        state = self._get_session(upload_id)
        if chunk_index < 0 or chunk_index >= state.total_chunks:
            raise AppError.bad_request("chunk_index out of range")
        chunk_path = state.temp_dir / f"chunk_{chunk_index:05d}"
        chunk_path.write_bytes(data)
        state.received_chunks.add(chunk_index)
        self._persist_sessions()
        return UploadSessionSchema(
            upload_id=upload_id,
            chunk_size=state.chunk_size,
            received_chunks=sorted(state.received_chunks),
        )

    def complete(
        self,
        project_id: uuid.UUID,
        upload_id: uuid.UUID,
        body: UploadCompleteRequest,
    ):
        state = self._get_session(upload_id)
        if state.project_id != project_id:
            raise AppError.forbidden(
                "Upload session does not belong to this project",
                code=ERR_DATASET_FORBIDDEN,
            )
        if len(state.received_chunks) < body.total_chunks:
            raise AppError.bad_request(
                "Not all chunks received",
                code=ERR_UPLOAD_INCOMPLETE,
                data={"received": len(state.received_chunks), "expected": body.total_chunks},
            )

        ds_id = uuid.uuid4()
        raw_dir = Path(self._storage.get_raw_path(str(project_id), str(ds_id)))
        merged = raw_dir / state.filename
        with merged.open("wb") as out:
            for i in range(body.total_chunks):
                part = state.temp_dir / f"chunk_{i:05d}"
                if not part.is_file():
                    raise AppError.bad_request(f"Missing chunk {i}", code=ERR_UPLOAD_INCOMPLETE)
                out.write(part.read_bytes())

        fmt = state.format_hint or _guess_format(state.filename)
        name = body.dataset_name or state.dataset_name or Path(state.filename).stem
        row = self._repo.create(
            dataset_id=ds_id,
            project_id=project_id,
            name=name,
            format=fmt,
            file_path=str(merged),
            num_samples=0,
            columns_meta=[],
            tags=body.tags,
            status="ready",
        )
        self._sessions.pop(upload_id, None)
        self._persist_sessions()
        return row


def _guess_format(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in {".csv", ".tsv"}:
        return "csv"
    if ext in {".json", ".jsonl"}:
        return "json"
    if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return "image"
    return "other"
