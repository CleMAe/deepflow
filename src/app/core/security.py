"""JWT token creation/verification and password hashing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from jose import jwt
from passlib.context import CryptContext

from src.infra.config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def _encode(payload: dict[str, Any], expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    claims = {**payload, "iat": now, "exp": now + expires_delta, "jti": str(uuid4())}
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID, username: str, role: str) -> tuple[str, int]:
    delta = timedelta(minutes=settings.access_token_expire_minutes)
    token = _encode({"sub": str(user_id), "username": username, "role": role, "type": "access"}, delta)
    return token, int(delta.total_seconds())


def create_refresh_token(user_id: UUID) -> str:
    delta = timedelta(days=settings.refresh_token_expire_days)
    return _encode({"sub": str(user_id), "type": "refresh"}, delta)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT. Raises JWTError on invalid/expired tokens."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
