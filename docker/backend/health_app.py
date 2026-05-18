"""Day 1 placeholder FastAPI app — replaced by P6 `app.main` when skeleton lands."""

from fastapi import FastAPI

app = FastAPI(title="DeepFlow API (placeholder)")


@app.get("/api/v1/health")
def health():
    return {"code": 0, "message": "success", "data": {"status": "ok", "service": "backend"}}
