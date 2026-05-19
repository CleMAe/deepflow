# Database Schema (P6)

Seven core tables aligned with `DeepFlow` DDL section 4.2 and `docs/api/openapi.yaml`.

| Table | Description |
|-------|-------------|
| `users` | Auth & RBAC |
| `projects` | Top-level workspace |
| `datasets` | Dataset metadata |
| `models` | Model configuration |
| `training_jobs` | Training lifecycle |
| `agents` | Agent configuration |
| `experiments` | Experiment records |

## Migrations

```bash
pip install -r requirements.txt
alembic upgrade head    # apply
alembic downgrade base  # rollback
alembic current         # show revision
```

Default dev DB: `sqlite:///./deepflow.db` (see `.env.example` for PostgreSQL).
