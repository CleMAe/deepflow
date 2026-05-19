from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import ERR_DATASET_INVALID_PARAM, AppError
from app.core.response import failure


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        rid = request.headers.get("X-Request-ID")
        body = failure(exc.code, exc.message, exc.data, request_id=rid)
        return JSONResponse(status_code=exc.http_status, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        rid = request.headers.get("X-Request-ID")
        body = failure(
            ERR_DATASET_INVALID_PARAM,
            "Invalid request parameters",
            {"errors": exc.errors()},
            request_id=rid,
        )
        return JSONResponse(status_code=400, content=body)
