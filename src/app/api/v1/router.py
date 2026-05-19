from fastapi import APIRouter

from app.api.v1.auth.router import router as auth_router
from app.api.v1.projects.router import router as projects_router
from app.api.v1.cleaning.router import router as cleaning_router
from app.api.v1.datasets.router import router as datasets_router
from app.api.v1.eda.router import router as eda_router
from app.api.v1.inference.router import router as inference_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(datasets_router)
api_router.include_router(cleaning_router)
api_router.include_router(eda_router)
api_router.include_router(inference_router)
