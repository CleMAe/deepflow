"""JWT and password helpers for P6 auth."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def _encode(payload: dict[str, Any]) -> str:
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(*, user_id: str, username: str, role: str) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = _encode(
        {
            "sub": user_id,
            "username": username,
            "role": role,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            "jti": str(uuid4()),
        }
    )
    return token, ACCESS_TOKEN_EXPIRE_MINUTES * 60


def create_refresh_token(*, user_id: str, username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return _encode(
        {
            "sub": user_id,
            "username": username,
            "role": role,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            "jti": str(uuid4()),
        }
    )


def decode_token(token: str, *, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    if payload.get("type") != expected_type:
        raise ValueError("Invalid token type")
    return payload
