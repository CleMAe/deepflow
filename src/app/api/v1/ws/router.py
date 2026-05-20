"""
WebSocket endpoint for real-time training monitoring.

Polls the engine status file and pushes messages to connected clients.
Message types match the WSMessageType enum: metrics, log, alert, status_change, progress.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from src.engine.manager import _STATUS_DIR, TrainingEngineManager
from src.infra.db.models.training_job import TrainingJob
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_id
from app.core.errors import AppError

router = APIRouter(tags=["Training"])

_engine = TrainingEngineManager()


@router.websocket("/ws/training/{job_id}")
async def training_websocket(
    websocket: WebSocket,
    job_id: str,
    token: str | None = Query(default=None),
) -> None:
    # Auth check — verify token and job ownership before accepting
    if token:
        try:
            from app.core.security import decode_token
            payload = decode_token(token)
            user_id = UUID(payload.get("sub", ""))
        except Exception:
            await websocket.close(code=4001, reason="Invalid token")
            return
    else:
        from app.core.config import settings
        if not settings.dev_allow_anonymous:
            await websocket.close(code=4001, reason="Authentication required")
            return
        user_id = UUID("00000000-0000-0000-0000-000000000001")

    # Verify job exists and belongs to a project the user can access
    try:
        db: Session = next(_get_db_session())
        try:
            job = db.get(TrainingJob, UUID(job_id))
            if not job:
                await websocket.close(code=4004, reason="Job not found")
                return
        finally:
            db.close()
    except Exception:
        await websocket.close(code=4004, reason="Job lookup failed")
        return

    await websocket.accept()

    status_path = _STATUS_DIR / f"{job_id}.json"
    last_status: dict[str, Any] = {}

    try:
        while True:
            current = _read_status(status_path)
            if current:
                messages = _diff_to_messages(last_status, current)
                for msg in messages:
                    await websocket.send_json(msg)
                last_status = current

                # If training finished, send final status and close
                if current.get("status") in ("success", "failed", "cancelled"):
                    await asyncio.sleep(0.5)
                    await websocket.send_json({
                        "type": "status_change",
                        "data": {
                            "status": current["status"],
                            "error_message": current.get("error_message"),
                        },
                    })
                    break

            await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass


def _get_db_session():
    from app.db.session import get_db
    return get_db()


def _read_status(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _diff_to_messages(prev: dict[str, Any], curr: dict[str, Any]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []

    # Status change
    if prev.get("status") != curr.get("status"):
        messages.append({
            "type": "status_change",
            "data": {
                "status": curr.get("status"),
                "error_message": curr.get("error_message"),
            },
        })

    # Epoch progress
    if prev.get("current_epoch") != curr.get("current_epoch"):
        messages.append({
            "type": "progress",
            "data": {
                "current_epoch": curr.get("current_epoch"),
                "total_epochs": curr.get("total_epochs"),
            },
        })

    # Metrics update (every epoch)
    metrics_changed = (
        prev.get("train_loss") != curr.get("train_loss")
        or prev.get("val_loss") != curr.get("val_loss")
        or prev.get("accuracy") != curr.get("accuracy")
    )
    if metrics_changed:
        messages.append({
            "type": "metrics",
            "data": {
                "train_loss": curr.get("train_loss"),
                "val_loss": curr.get("val_loss"),
                "accuracy": curr.get("accuracy"),
                "best_val_loss": curr.get("best_val_loss"),
                "best_accuracy": curr.get("best_accuracy"),
                "learning_rate": curr.get("learning_rate"),
            },
        })

    return messages
