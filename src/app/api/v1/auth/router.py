"""Auth routes — /api/v1/auth/* (P6 contract)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.response import success
from app.db.session import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


def _auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/login", summary="Login with username and password")
def login(body: LoginRequest, svc: AuthService = Depends(_auth_service)) -> dict:
    tokens = svc.login(body.username, body.password)
    return success(tokens.model_dump())


@router.post("/register", status_code=status.HTTP_201_CREATED, summary="Register a new user")
def register(body: RegisterRequest, svc: AuthService = Depends(_auth_service)) -> dict:
    user = svc.register(body)
    return success(user.model_dump(mode="json"))


@router.post("/refresh", summary="Refresh access token")
def refresh(body: RefreshRequest, svc: AuthService = Depends(_auth_service)) -> dict:
    tokens = svc.refresh(body.refresh_token)
    return success(tokens.model_dump())


@router.get("/me", summary="Get current user info")
def me(
    current_user: Annotated[UUID, Depends(get_current_user)],
    svc: AuthService = Depends(_auth_service),
) -> dict:
    user = svc.get_user(current_user)
    return success(user.model_dump(mode="json"))
