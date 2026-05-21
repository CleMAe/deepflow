"""Unified 8-digit error codes (module-category-sequence).

Per OpenAPI contract and P6 prompt:
  XX-YY-ZZZ
  XX  = module   (10=auth, 20=project, 30=dataset, 40=model, 50=training, 60=inference, 70=agent, 90=system)
  YY  = category (01=param, 02=not-found, 03=permission, 04=logic, 05=system)
  ZZZ = sequence
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def error_code(module: int, category: int, sequence: int) -> int:
    """Encode XX-YY-ZZZ as 8-digit integer, e.g. 30-02-001 → 30002001."""
    return module * 1_000_000 + category * 1_000 + sequence


# ── Auth (10) ────────────────────────────────────────────────
ERR_AUTH_INVALID_PARAM = error_code(10, 1, 1)
ERR_AUTH_CREDENTIALS = error_code(10, 2, 1)
ERR_AUTH_MISSING = error_code(10, 3, 1)
ERR_AUTH_INVALID = error_code(10, 3, 2)
ERR_AUTH_USERNAME_EXISTS = error_code(10, 4, 1)

# ── Project (20) ─────────────────────────────────────────────
ERR_PROJECT_NOT_FOUND = error_code(20, 2, 1)
ERR_PROJECT_INVALID_PARAM = error_code(20, 1, 1)
ERR_PROJECT_FORBIDDEN = error_code(20, 3, 1)

# ── Dataset (30) ─────────────────────────────────────────────
ERR_DATASET_NOT_FOUND = error_code(30, 2, 1)
ERR_DATASET_INVALID_PARAM = error_code(30, 1, 1)
ERR_DATASET_FORBIDDEN = error_code(30, 3, 1)
ERR_UPLOAD_NOT_FOUND = error_code(30, 2, 2)
ERR_UPLOAD_INCOMPLETE = error_code(30, 4, 1)

# ── Model (40) ───────────────────────────────────────────────
ERR_MODEL_NOT_FOUND = error_code(40, 2, 1)
ERR_MODEL_INVALID_PARAM = error_code(40, 1, 1)

# ── Training (50) ────────────────────────────────────────────
ERR_TRAINING_JOB_NOT_FOUND = error_code(50, 2, 1)
ERR_TRAINING_INVALID_TRANSITION = error_code(50, 1, 1)

# ── Inference (60) ───────────────────────────────────────────
ERR_INFERENCE_TASK_NOT_FOUND = error_code(60, 2, 1)
ERR_INFERENCE_INVALID_PARAM = error_code(60, 1, 1)
ERR_INFERENCE_MODEL_NOT_FOUND = error_code(60, 2, 2)
ERR_INFERENCE_CHECKPOINT_NOT_FOUND = error_code(60, 2, 3)
ERR_INFERENCE_DATASET_NOT_FOUND = error_code(60, 2, 4)
ERR_INFERENCE_MODEL_LOAD_FAILED = error_code(60, 5, 1)
ERR_INFERENCE_EXPORT_FAILED = error_code(60, 5, 2)

# ── Agent (70) ───────────────────────────────────────────────
ERR_AGENT_NOT_FOUND = error_code(70, 2, 1)
ERR_AGENT_INVALID_PARAM = error_code(70, 1, 1)
ERR_AGENT_INVALID_STATUS = error_code(70, 1, 2)
ERR_AGENT_TOOL_NOT_FOUND = error_code(70, 2, 2)
ERR_AGENT_FORBIDDEN = error_code(70, 3, 1)
ERR_AGENT_TOOL_BIND_FAILED = error_code(70, 4, 1)
ERR_AGENT_CHAT_FAILED = error_code(70, 4, 2)
ERR_AGENT_TOOL_ROUND_LIMIT = error_code(70, 4, 3)
ERR_AGENT_PROMPT_RENDER_FAILED = error_code(70, 4, 4)

# ── System / Infra (90) ──────────────────────────────────────
ERR_SYSTEM_DB_UNAVAILABLE = error_code(90, 5, 1)
ERR_SYSTEM_INTERNAL = error_code(90, 5, 2)


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
    def forbidden(cls, message: str, *, code: int = ERR_PROJECT_FORBIDDEN, data: Any = None) -> AppError:
        return cls(403, code, message, data)

    @classmethod
    def unauthorized(cls, message: str, *, code: int = ERR_AUTH_MISSING) -> AppError:
        return cls(401, code, message, None)

    @classmethod
    def internal(cls, message: str, *, code: int = ERR_SYSTEM_INTERNAL, data: Any = None) -> AppError:
        return cls(500, code, message, data)
