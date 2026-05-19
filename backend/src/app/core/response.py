from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """Matches `docs/api/openapi.yaml` → components.schemas.ApiResponse."""

    code: int = 0
    message: str = "success"
    data: Any | None = None
    request_id: str = Field(default_factory=lambda: str(uuid4()))


def success(data: Any = None, message: str = "success", request_id: str | None = None) -> dict[str, Any]:
    rid = request_id or str(uuid4())
    return ApiResponse(code=0, message=message, data=data, request_id=rid).model_dump()


def failure(
    code: int,
    message: str,
    data: Any = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    rid = request_id or str(uuid4())
    return ApiResponse(code=code, message=message, data=data, request_id=rid).model_dump()
