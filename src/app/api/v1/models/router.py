from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_project_access
from app.core.response import success
from app.schemas.model import (
    ModelCreate,
    ModelUpdate,
    ModelValidateRequest,
    PretrainedLoadRequest,
)
from app.services.model_mock import MockModelLibrary, MockModelService

model_service = MockModelService()
model_library = MockModelLibrary()

library_router = APIRouter(prefix="/models/library", tags=["ModelLibrary"])
project_models_router = APIRouter(prefix="/projects/{project_id}/models", tags=["Models"])


@library_router.get("")
async def list_library(
    task_type: str | None = Query(None, enum=["classification", "regression", "object_detection", "segmentation"]),
    search: str | None = Query(None),
):
    models = model_library.list_models(task_type=task_type, search=search)
    return success(models)


@library_router.get("/{model_id}")
async def get_library_model(model_id: str):
    model = model_library.get_model(model_id)
    if not model:
        from app.core.errors import ERR_MODEL_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_MODEL_NOT_FOUND, message=f"Library model '{model_id}' not found")
    return success(model)


@project_models_router.get("")
async def list_project_models(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: UUID = Depends(require_project_access),
):
    result = model_service.list_project_models(str(project_id), page, page_size)
    return success(result)


@project_models_router.post("")
async def create_project_model(
    project_id: UUID,
    body: ModelCreate,
    _: UUID = Depends(require_project_access),
):
    model = model_service.create_model(str(project_id), body.model_dump())
    return success(model)


@project_models_router.get("/{m_id}")
async def get_project_model(
    project_id: UUID,
    m_id: UUID,
    _: UUID = Depends(require_project_access),
):
    model = model_service.get_model(str(m_id))
    if not model or model.get("project_id") != str(project_id):
        from app.core.errors import ERR_MODEL_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_MODEL_NOT_FOUND, message=f"Model '{m_id}' not found")
    return success(model)


@project_models_router.put("/{m_id}")
async def update_project_model(
    project_id: UUID,
    m_id: UUID,
    body: ModelUpdate,
    _: UUID = Depends(require_project_access),
):
    model = model_service.update_model(str(m_id), body.model_dump(exclude_none=True))
    if not model:
        from app.core.errors import ERR_MODEL_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_MODEL_NOT_FOUND, message=f"Model '{m_id}' not found")
    return success(model)


@project_models_router.post("/{m_id}/validate")
async def validate_model_config(
    project_id: UUID,
    m_id: UUID,
    body: ModelValidateRequest,
    _: UUID = Depends(require_project_access),
):
    model = model_service.get_model(str(m_id))
    if not model:
        from app.core.errors import ERR_MODEL_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_MODEL_NOT_FOUND, message=f"Model '{m_id}' not found")

    result = model_library.validate_config(model["arch_type"], body.params_cfg)
    return success(result.model_dump())


@project_models_router.post("/{m_id}/pretrained")
async def load_pretrained_weights(
    project_id: UUID,
    m_id: UUID,
    body: PretrainedLoadRequest,
    _: UUID = Depends(require_project_access),
):
    model = model_service.get_model(str(m_id))
    if not model:
        from app.core.errors import ERR_MODEL_NOT_FOUND

        from app.core.response import failure

        return failure(code=ERR_MODEL_NOT_FOUND, message=f"Model '{m_id}' not found")

    model["pretrained"] = True
    model["pretrained_source"] = f"{body.source}:{body.repo_id}"
    model["model_path"] = f"/mock/models/{m_id}/pretrained.pth"

    return success(
        {
            "status": "ready",
            "model_path": model["model_path"],
        }
    )
