from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.response import success
from app.db.seed import seed_demo_datasets
from app.db.session import get_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = next(get_db())
    try:
        seed_demo_datasets(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="P7 Data API — OpenAPI-aligned, Protocol DI, DDL-backed store",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return success(
        {
            "status": "ok",
            "mock_mode": settings.mock_mode,
            "dev_allow_anonymous": settings.dev_allow_anonymous,
        }
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)
