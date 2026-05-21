"""Auth API routes — login, register, refresh, me."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.core.errors import (
    ERR_AUTH_CREDENTIALS,
    ERR_AUTH_INVALID,
    ERR_AUTH_USERNAME_EXISTS,
    AppError,
)
from app.core.response import success
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair, UserOut
from src.infra.db.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user:
        verify_password("dummy", hash_password("dummy"))
        raise AppError(http_status=401, code=ERR_AUTH_CREDENTIALS, message="Invalid username or password")
    if not verify_password(body.password, user.password_hash):
        raise AppError(http_status=401, code=ERR_AUTH_CREDENTIALS, message="Invalid username or password")
    access_token, expires_in = create_access_token(user.id, user.username, user.role.value)
    refresh_token = create_refresh_token(user.id)
    return success(
        TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        ).model_dump()
    )


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise AppError.bad_request("Username already exists", code=ERR_AUTH_USERNAME_EXISTS)
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success(_user_out(user).model_dump())


@router.post("/refresh")
async def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        raise AppError.unauthorized("Invalid or expired refresh token", code=ERR_AUTH_INVALID)
    if payload.get("type") != "refresh":
        raise AppError.unauthorized("Not a refresh token", code=ERR_AUTH_INVALID)

    user_id = UUID(payload["sub"])
    user = db.get(User, user_id)
    if not user:
        raise AppError.unauthorized("User not found", code=ERR_AUTH_INVALID)

    access_token, expires_in = create_access_token(user.id, user.username, user.role.value)
    refresh_token = create_refresh_token(user.id)
    return success(
        TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        ).model_dump()
    )


@router.get("/me")
async def me(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise AppError.unauthorized("User not found")
    return success(_user_out(user).model_dump())


def _user_out(u: User) -> UserOut:
    return UserOut(id=u.id, username=u.username, role=u.role.value, created_at=u.created_at)
