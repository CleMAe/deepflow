"""Authentication business logic."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ERR_AUTH_DUPLICATE_USER, ERR_AUTH_INVALID, AppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.schemas.auth import RegisterRequest, TokenPair, UserOut
from src.infra.db.models.user import User


class AuthService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def register(self, body: RegisterRequest) -> UserOut:
        existing = self._db.scalar(select(User).where(User.username == body.username))
        if existing is not None:
            raise AppError.bad_request(
                "Username already registered",
                code=ERR_AUTH_DUPLICATE_USER,
            )
        user = User(
            username=body.username,
            password_hash=hash_password(body.password),
            role=body.role,
        )
        self._db.add(user)
        self._db.flush()
        self._db.refresh(user)
        return UserOut.model_validate(user)

    def login(self, username: str, password: str) -> TokenPair:
        user = self._db.scalar(select(User).where(User.username == username))
        if user is None or not verify_password(password, user.password_hash):
            raise AppError.unauthorized("Invalid username or password", code=ERR_AUTH_INVALID)
        access, expires_in = create_access_token(
            user_id=str(user.id),
            username=user.username,
            role=user.role.value,
        )
        refresh = create_refresh_token(
            user_id=str(user.id),
            username=user.username,
            role=user.role.value,
        )
        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=expires_in,
        )

    def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except ValueError as exc:
            raise AppError.unauthorized("Invalid refresh token", code=ERR_AUTH_INVALID) from exc
        user_id = payload.get("sub")
        user = self._db.get(User, UUID(str(user_id)))
        if user is None:
            raise AppError.unauthorized("Invalid refresh token", code=ERR_AUTH_INVALID)
        access, expires_in = create_access_token(
            user_id=str(user.id),
            username=user.username,
            role=user.role.value,
        )
        new_refresh = create_refresh_token(
            user_id=str(user.id),
            username=user.username,
            role=user.role.value,
        )
        return TokenPair(
            access_token=access,
            refresh_token=new_refresh,
            expires_in=expires_in,
        )

    def get_user(self, user_id: UUID) -> UserOut:
        user = self._db.get(User, user_id)
        if user is None:
            raise AppError.unauthorized("User not found", code=ERR_AUTH_INVALID)
        return UserOut.model_validate(user)
