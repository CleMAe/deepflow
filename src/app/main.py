"""DeepFlow FastAPI application — main entry point.

Four-layer architecture (per CLAUDE.md):
  Interaction → Service → Engine → Data

This module lives at the Service layer. It wires together:
  - CORS (dev-wide open; production tightened via env)
  - Exception handlers (unified 8-digit error codes per OpenAPI contract)
  - DB session init (canonical infra models via src.infra.db)
  - Router composition (P6 auth/projects + P7 datasets/cleaning/EDA + P8 training/inference)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager, closing

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.errors import ERR_SYSTEM_DB_UNAVAILABLE
from app.core.response import failure, success
from app.db.seed import seed_demo_datasets
from app.db.session import get_db, init_db
from src.infra.config import DEFAULT_JWT_SECRET_KEY

logger = logging.getLogger(__name__)


def warn_if_insecure_jwt_secret() -> None:
    database_url = settings.database_url.lower()
    if "sqlite" not in database_url and settings.jwt_secret_key == DEFAULT_JWT_SECRET_KEY:
        logger.warning(
            "JWT secret key is still using the development default while DATABASE_URL is not SQLite; "
            "set JWT_SECRET_KEY or JWT_SECRET before production/integration startup."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    warn_if_insecure_jwt_secret()
    import src.infra.db.models  # noqa: F401 — register all models with Base.metadata
    init_db()
    with closing(get_db()) as db_gen:
        db = next(db_gen)
        seed_demo_datasets(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.3.0",
    description="DeepFlow — end-to-end deep learning platform (Data → Clean → Model → Train → Inference → Agent)",
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


@app.get("/api/v1/health")
async def health():
    """Health check with database connectivity verification.

    Returns:
      - 200 with `db: "connected"` when DB is reachable
      - 503 with `db: "disconnected"` when DB is down
    """
    db_status = "disconnected"
    try:
        with closing(get_db()) as db_gen:
            db = next(db_gen)
            db.execute(text("SELECT 1"))
            db.commit()
            db_status = "connected"
    except Exception:
        db_status = "disconnected"

    response_data = {
        "status": "ok" if db_status == "connected" else "degraded",
        "db": db_status,
        "mock_mode": settings.mock_mode,
        "dev_allow_anonymous": settings.dev_allow_anonymous,
        "version": "0.3.0",
    }

    if db_status != "connected":
        body = failure(code=ERR_SYSTEM_DB_UNAVAILABLE, message="Database unavailable", data=response_data)
        return JSONResponse(status_code=503, content=body)

    return success(response_data)


app.include_router(api_router, prefix=settings.api_v1_prefix)
