# DeepFlow P7 — Data API

OpenAPI-aligned data layer with Protocol-based DI and DDL-backed persistence.

## Quick start

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=src
uvicorn app.main:app --reload --port 8000
```

- Swagger: http://127.0.0.1:8000/docs  
- Demo project: `11111111-1111-1111-1111-111111111111`

## Architecture

| Layer | Role |
|-------|------|
| `api/v1/*/router.py` | HTTP only; `Depends()` for services + auth |
| `services/` | Business logic; consumes `StorageProtocol` via `MockFileStorage` |
| `repositories/` | SQLAlchemy ORM (no raw SQL concatenation) |
| `db/models.py` | `datasets` table fields match P6 DDL |
| `core/errors.py` | 8-digit codes (`30002001` = 30-02-001) |

## Configuration

| Env | Default | Meaning |
|-----|---------|---------|
| `DEV_ALLOW_ANONYMOUS` | `true` | Skip JWT (Day1 dev); set `false` before prod |
| `DATABASE_URL` | `sqlite:///./storage/deepflow_p7.db` | Local DB until P6 Alembic |
| `STORAGE_ROOT` | `./storage` | File layout per P6 spec |

## P6 integration

Replace in `api/deps.py`:

- `get_storage()` → P6 `RealFileStorage`
- `get_current_user_id()` → P6 JWT decoder
- `get_db()` → P6 session factory

Mount: `app.include_router(api_router, prefix="/api/v1")`
