import asyncio
import json
import time
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws/training", tags=["Training"])


@router.websocket("/{job_id}")
async def training_websocket(websocket: WebSocket, job_id: str):
    await websocket.accept()

    epoch = 0
    try:
        while True:
            epoch += 1
            step = epoch * 10

            train_loss = round(2.0 / epoch + 0.1, 4)
            val_loss = round(2.2 / epoch + 0.15, 4)
            accuracy = round(min(0.5 + epoch * 0.05, 0.95), 4)

            events = [
                {
                    "type": "progress",
                    "data": {"epoch": epoch, "step": step, "total_epochs": 10},
                },
                {
                    "type": "metrics",
                    "data": {
                        "epoch": epoch,
                        "step": step,
                        "train_loss": train_loss,
                        "val_loss": val_loss,
                        "accuracy": accuracy,
                        "learning_rate": 0.001,
                        "gpu_util": 78.5,
                        "gpu_memory": 4520.0,
                        "cpu_util": 35.2,
                        "memory_util": 62.1,
                        "throughput": "156 samples/sec",
                        "eta": f"{max(0, 10 - epoch) * 30}s",
                    },
                },
                {
                    "type": "log",
                    "data": {
                        "message": f"[Epoch {epoch}/10] train_loss={train_loss:.4f} val_loss={val_loss:.4f} accuracy={accuracy:.4f}"
                    },
                },
                {
                    "type": "status_change",
                    "data": {"status": "running", "epoch": epoch},
                },
            ]

            if epoch == 1:
                events.append(
                    {
                        "type": "alert",
                        "data": {"level": "info", "message": "Training started successfully"},
                    }
                )

            if train_loss < 0.25:
                events.append(
                    {
                        "type": "alert",
                        "data": {
                            "level": "warning",
                            "message": f"Loss is very low ({train_loss:.4f}), possible overfitting",
                        },
                    }
                )

            for event in events:
                await websocket.send_text(json.dumps(event))
                await asyncio.sleep(0.3)

            if epoch >= 10:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "status_change",
                            "data": {"status": "success", "epoch": epoch},
                        }
                    )
                )
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "alert",
                            "data": {"level": "info", "message": "Training completed successfully"},
                        }
                    )
                )
                break

            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
