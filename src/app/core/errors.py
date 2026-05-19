"""Unified 8-digit error codes (module-category-sequence)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4


def error_code(module: int, category: int, sequence: int) -> int:
    """Encode XX-YY-ZZZ as 8-digit integer, e.g. 30-02-001 → 30002001."""
    return module * 1_000_000 + category * 1_000 + sequence


# Project module (20)
ERR_PROJECT_NOT_FOUND = error_code(20, 2, 1)
ERR_PROJECT_FORBIDDEN = error_code(20, 3, 1)

# Dataset module (30)
ERR_DATASET_NOT_FOUND = error_code(30, 2, 1)
ERR_DATASET_INVALID_PARAM = error_code(30, 1, 1)
ERR_UPLOAD_NOT_FOUND = error_code(30, 2, 2)
ERR_UPLOAD_INCOMPLETE = error_code(30, 4, 1)
ERR_DATASET_FORBIDDEN = error_code(30, 3, 1)

# Auth (10)
ERR_AUTH_MISSING = error_code(10, 3, 1)
ERR_AUTH_INVALID = error_code(10, 3, 2)
ERR_AUTH_DUPLICATE_USER = error_code(10, 4, 1)


@dataclass
class AppError(Exception):
    http_status: int
    code: int
    message: str
    data: Any = None

    @classmethod
    def not_found(cls, message: str, *, code: int = ERR_DATASET_NOT_FOUND, data: Any = None) -> AppError:
        return cls(404, code, message, data)

    @classmethod
    def bad_request(cls, message: str, *, code: int = ERR_DATASET_INVALID_PARAM, data: Any = None) -> AppError:
        return cls(400, code, message, data)

    @classmethod
    def forbidden(cls, message: str, *, code: int = ERR_DATASET_FORBIDDEN, data: Any = None) -> AppError:
        return cls(403, code, message, data)

    @classmethod
    def unauthorized(cls, message: str, *, code: int = ERR_AUTH_MISSING) -> AppError:
        return cls(401, code, message, None)
