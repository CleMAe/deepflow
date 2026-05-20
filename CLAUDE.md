# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DeepFlow** is an end-to-end deep learning platform targeting business developers. The core pipeline is: Data Upload → Data Cleaning → Model Building → Training → Inference → Agent Construction. The authoritative plan is `DeepFlow_实施计划_V1.0_DSv4OC.md`; the PRD is `DeepFlow_PRD_V1.0.md`.

## Architecture

Four-layer architecture with strict decoupling:

- **Interaction Layer (Frontend)**: React 18 + TypeScript + Vite, Ant Design 5.x, Zustand, ECharts, MSW for mock
- **Service Layer (Backend API)**: Python 3.10 + FastAPI, SQLAlchemy 2.0 + Alembic, PostgreSQL 15 (SQLite for dev)
- **Engine Layer (Core)**: PyTorch 2.x training engine (runs as subprocess via `src/engine/`), ONNX Runtime inference, Agent engine (OpenAI-compatible via LiteLLM)
- **Data Layer**: PostgreSQL for metadata, local filesystem for files/models (no S3/MinIO in V1.0), UUID-based directory structure

Key decoupling: all inter-module communication via REST API (no in-process function calls). Real-time monitoring via WebSocket push (no polling). Large files shared via filesystem UUID paths, not API transfer.

## Current Module Status (Day 3 — as of 2026-05-20)

### Progress vs Plan Summary

**Day 1 (地基日)** — Target: Contract freeze, scaffold, mock API, at least 1 FE page
- ✅ Contract frozen (`openapi.yaml`, `protocols.py`, Alembic migration)
- ✅ FastAPI skeleton + `/health` endpoint + DB connection
- ✅ FE scaffold (Vite + React + routing + MSW)
- ✅ Docker Compose (app + db + frontend + gpu-train)
- ✅ Mock services for cleaning/EDA/inference
- ✅ FE Login/Register + Dashboard + Data management pages
- ✅ P8 router骨架 merged

**Day 2 (功能日)** — Target: All P0 BE APIs return real data; FE P0 page structures complete; Agent engine core
- ✅ Training engine: real PyTorch subprocess + state machine + checkpoint + early stopping
- ✅ Model library: real SQLAlchemy CRUD + 6 architectures
- ✅ Experiments: real CRUD + comparison + auto-create on training completion
- ✅ WebSocket: real status-file polling + diff-based push
- ✅ Dataset upload: real UploadService + DatasetService
- ✅ Agent engine: tech design published (`docs/backend/agent-engine-tech-design.md`)
- ✅ Auth API: real JWT auth (login/register/refresh/me) — merged PR #22
- ✅ Projects CRUD: full CRUD with ownership scoping — merged PR #22
- ✅ CI pipeline: GitHub Actions lint + integration test + Docker build — on `feat/day2-devops` branch
- ✅ API integration tests: auth/projects/datasets — on `feat/day2-devops` branch
- ❌ Cleaning: still MockCleaningService
- ❌ EDA: still mock
- ❌ Inference: still mock
- ❌ Agent implementation: not started
- ❌ P3/P4 FE pages: still placeholders (Cleaning/EDA, Models, Training)

**Day 3 (集成日) — in progress**
- ✅ P6 Auth+Projects API shipped
- ❌ P9 CI+tests on `feat/day2-devops` branch, not yet merged to main
- ❌ P7 cleaning/EDA real engine
- ❌ P3/P4 real FE pages
- ❌ P1 Agent implementation
- ❌ P8 inference engine

### Backend (merged to main)

| Module | Path | Status | Gap |
|--------|------|--------|-----|
| Dataset upload/CRUD | `src/app/api/v1/datasets/` | ✅ Real (UploadService + DatasetService) | — |
| Data cleaning | `src/app/api/v1/cleaning/` | ❌ Mock (`MockCleaningService`) | P7 — pandas engine not started |
| EDA | `src/app/api/v1/eda/` | ❌ Mock (no real computation) | P7 — stats engine not started |
| Inference | `src/app/api/v1/inference/` | ❌ Mock endpoints | P8 — no real inference yet |
| Training jobs | `src/app/api/v1/training/` | ✅ Real (PyTorch subprocess + state machine + checkpoint + early stopping) | — |
| Model library | `src/app/api/v1/models/` | ✅ Real (SQLAlchemy CRUD + 6 architectures) | — |
| Experiments | `src/app/api/v1/experiments/` | ✅ Real (CRUD + comparison + auto-create) | — |
| WebSocket | `src/app/api/v1/ws/` | ✅ Real (status-file polling + diff-based push) | — |
| Auth | `src/app/api/v1/auth/` | ✅ Real (JWT login/register/refresh/me + bcrypt) | — |
| Projects | `src/app/api/v1/projects/` | ✅ Real (CRUD + ownership scoping + pagination) | — |
| Agent | — | ❌ Not started (design doc only) | P1 — implementation pending |

### DevOps & Testing (on `feat/day2-devops` branch, not yet merged to main)

| Item | Path | Status |
|------|------|--------|
| CI pipeline | `.github/workflows/ci.yml` | ✅ lint + integration-test + Docker build (170 lines) |
| Auth API tests | `backend/tests/api/test_auth.py` | ✅ 197 lines — login/register/refresh/me + error cases |
| Projects API tests | `backend/tests/api/test_projects.py` | ✅ 221 lines — CRUD + ownership + pagination |
| Datasets API tests | `backend/tests/api/test_datasets.py` | ✅ 345 lines — upload + CRUD + preview |
| Test factories | `backend/tests/factories/` | ✅ user/project/dataset factories |
| Docker fixes | `docker/backend/Dockerfile` | ✅ deps path alignment |

### Frontend (merged to main)

| Page | Path | Status | Gap |
|------|------|--------|-----|
| Dashboard | `DashboardPage.tsx` | ✅ Complete | — |
| Login/Register | `LoginPage.tsx` / `RegisterPage.tsx` | ✅ Complete | — |
| Data management | `ProjectDataPage.tsx` | ✅ Upload + list (basic) | — |
| Cleaning & EDA | `ProjectCleaningPage.tsx` | ❌ Placeholder (3 tab labels only) | P3 — no real UI |
| Model building | `ProjectModelsPage.tsx` | ❌ Placeholder (1 line text) | P4 — no real UI |
| Training monitoring | `ProjectTrainingPage.tsx` | ❌ Placeholder (1 line text) | P4 — no real UI |
| Inference testing | `ProjectInferencePage.tsx` | ✅ Evaluation + online test + batch + confusion matrix | — |
| Agent management | `ProjectAgentsPage.tsx` | ✅ Dialog + tool binding UI | — |

**Note**: P2 frontend PR #23 added CodeEditor, CommonModal, MSW handlers (models/training/experiments), Ant Design theme, and FileUpload chunk upload — but some of these were reverted on the `feat/day2-devops` branch. The main branch has the P2 additions.

### Feature Completion Summary

**Backend (7/11 done)**
- ✅ Dataset upload/CRUD
- ✅ Training jobs (subprocess + state machine + checkpoint + early stopping)
- ✅ Model library (6 architectures)
- ✅ Experiments (CRUD + comparison + auto-create)
- ✅ WebSocket (status-file polling + diff-based push)
- ✅ Auth (JWT login/register/refresh/me)
- ✅ Projects (CRUD + ownership scoping)
- ❌ Data cleaning (still mock)
- ❌ EDA (still mock)
- ❌ Inference (still mock)
- ❌ Agent (design doc only)

**Frontend (5/8 done)**
- ✅ Dashboard
- ✅ Login/Register
- ✅ Data management
- ✅ Inference testing
- ✅ Agent management
- ❌ Cleaning & EDA (placeholder)
- ❌ Model building (placeholder)
- ❌ Training monitoring (placeholder)

### Key Blockers

1. **P7 (Cleaning + EDA)**: Still mock. P7 branch (`feature/p7`) is stale and hasn't merged latest main. Blocks the P0 full pipeline (upload→clean→model→train→infer).
2. **P3 (Cleaning/EDA FE)**: Page still placeholder. Blocks end-to-end data flow testing.
3. **P4 (Model + Training FE)**: Both pages still placeholder. Blocks training workflow testing.
4. **P8 (Inference)**: Still mock. Needed for Agent tool wrapping.
5. **P1 (Agent)**: Design doc only, no implementation. Highest priority feature per plan.
6. **P9 (CI/tests)**: On `feat/day2-devops` branch but not yet merged to main — needs PR and review.

## Source Code Layout

```
src/
├── engine/                  # Training engine (subprocess)
│   ├── train_worker.py      #   PyTorch training loop (entry: python -m src.engine.train_worker)
│   └── manager.py           #   Subprocess lifecycle manager (TrainingEngineManager)
├── infra/
│   ├── config.py            # Canonical pydantic-settings (jwt_secret_key, database_url, etc.)
│   └── db/
│       ├── models/          # SQLAlchemy 2.0 ORM models (single canonical source)
│       │   ├── user.py
│       │   ├── project.py
│       │   ├── dataset.py
│       │   ├── ml_model.py
│       │   ├── training_job.py
│       │   ├── experiment.py
│       │   └── agent.py
│       ├── base.py          # DeclarativeBase + mixins (UUIDPrimaryKeyMixin, TimestampMixin)
│       └── session.py       # Engine + session factory
├── app/
│   ├── main.py              # FastAPI app (lifespan, CORS, /api/v1/health with DB check)
│   ├── api/
│   │   ├── deps.py          # DI: get_storage, get_dataset_service, get_training_service, etc.
│   │   └── v1/              # Routers by module (auth, projects, datasets, cleaning, eda, inference, training, models, experiments, ws)
│   ├── core/
│   │   ├── config.py        # Re-exports src.infra.config.settings
│   │   ├── errors.py        # 8-digit error codes (10=auth .. 90=system) + AppError
│   │   ├── response.py      # success() / failure() helpers
│   │   ├── security.py      # JWT creation/verification + bcrypt password hashing
│   │   └── exception_handlers.py
│   ├── schemas/             # Pydantic request/response models
│   ├── services/            # Business logic
│   ├── repositories/        # DB queries
│   ├── mappers/             # ORM → schema mapping
│   └── db/
│       ├── session.py       # Delegates to infra session
│       └── seed.py          # Demo data seeding
├── shared/
│   └── protocols.py         # Inter-module Protocol interfaces (frozen Day 1)
├── agent/                   # Agent engine (P1 — not yet implemented, no directory yet)
│   ├── router.py            #   11 API endpoints (planned)
│   ├── service.py           #   Agent business logic (planned)
│   ├── chat_engine.py       #   SSE streaming + tool-call loop (planned)
│   ├── tool_wrapper.py      #   Model → OpenAI function-calling tool (planned)
│   ├── llm_provider.py      #   LiteLLMProvider + MockLLMProvider (planned)
│   └── prompt_manager.py    #   Template CRUD + $variable rendering (planned)
frontend/
├── src/
│   ├── pages/               # React page components
│   ├── api/                 # Axios API wrappers + generated types
│   ├── mocks/               # MSW handlers per module
│   └── lib/                 # Axios instance, Zustand stores
```

## API Contract

The single source of truth is `docs/api/openapi.yaml` (maintained by P1/Tech Lead), frozen on Day 1. All endpoints use prefix `/api/v1`. Responses follow `{code, message, data, request_id}`. Pagination is `{page, page_size, total, items[]}`. Errors use 8-digit codes `XX-YY-ZZZ` (module + category + sequence). Auth via `Authorization: Bearer <JWT>`.

Current route count: **55 registered endpoints** (54 REST + 1 WebSocket) across auth, projects, datasets, cleaning, EDA, inference, training, models, experiments, WebSocket, and health. Agent endpoints (11) not yet implemented — see `docs/backend/agent-engine-tech-design.md`.

## Error Code Modules

| Module | XX | Key Codes |
|--------|-----|-----------|
| Auth | 10 | ERR_AUTH_MISSING (10-3-1), ERR_AUTH_INVALID (10-3-2), ERR_AUTH_USERNAME_EXISTS (10-4-1) |
| Project | 20 | ERR_PROJECT_NOT_FOUND (20-2-1), ERR_PROJECT_FORBIDDEN (20-3-1) |
| Dataset | 30 | ERR_DATASET_NOT_FOUND (30-2-1), ERR_UPLOAD_INCOMPLETE (30-4-1) |
| Model | 40 | ERR_MODEL_NOT_FOUND (40-2-1) |
| Training | 50 | ERR_TRAINING_JOB_NOT_FOUND (50-2-1), ERR_TRAINING_INVALID_TRANSITION (50-1-1) |
| Inference | 60 | ERR_INFERENCE_TASK_NOT_FOUND (60-2-1) |
| Agent | 70 | ERR_AGENT_NOT_FOUND (70-2-1) |
| System | 90 | ERR_SYSTEM_DB_UNAVAILABLE (90-5-1), ERR_SYSTEM_INTERNAL (90-5-2) |

## Training Engine Architecture

The training engine runs as a **subprocess**, isolated from the FastAPI process:

1. API layer calls `TrainingEngineManager.start_training()` → spawns `python -m src.engine.train_worker`
2. Worker writes progress to a JSON status file (`/tmp/deepflow_training/<job_id>.json`)
3. API polls the status file on GET requests and WebSocket connections
4. State machine enforces valid transitions: `pending → running → paused/success/failed/cancelled`
5. On terminal state, an `Experiment` record is auto-created

Supported models: ResNet-18/34/50, EfficientNet-B0/B1, MLP. Supports mixed precision (AMP), gradient accumulation, LR schedulers, early stopping, and checkpoint saving.

## Config Architecture

All settings live in **`src/infra/config.py`** (canonical source). `src/app/core/config.py` only re-exports `settings` from infra. Key fields: `database_url`, `storage_root`, `jwt_secret_key`, `jwt_algorithm`, `access_token_expire_minutes`, `dev_allow_anonymous`, `mock_mode`.

## Git Workflow

Branch strategy:
- `main` — production-ready, no direct push
- `feat/<module>` — feature branches, lifespan ≤ 1 day
- `fix/<module>` — fix branches

**All code changes must go through a branch + PR. Never push directly to main.**

Branch naming: `feat/<module>-<owner>-<short-task>` or `fix/<module>-<owner>-<short-task>`

PR rules: at least 1 reviewer approve; P1 reviews all BE PRs, P2 reviews all FE PRs. Commit format: `feat(module): description` / `fix(module): description` / `docs: description`.

No code may sit unpushed for more than 2 hours.

## Key Protocols and Conventions

- **Shared interfaces**: Python Protocol classes in `src/shared/protocols.py` (frozen Day 1 10:00)
- **File storage layout**: `{STORAGE_ROOT}/projects/{project_uuid}/datasets|models|experiments/...`
- **WebSocket training messages**: JSON with `type` (metrics/log/alert/status_change/progress) + `data`
- **Training engine**: runs as subprocess; state machine with enum + DB transaction consistency
- **Async task states**: `pending / running / success / failed / cancelled / paused`
- **Mock strategy**: FE uses MSW handlers in `@/mocks/handlers/`; BE tests use pytest + factory_boy + SQLite; synthetic data generator at `scripts/gen_synthetic_data.py`
- **DB models**: Single canonical source in `src/infra/db/models/` — no duplicate model definitions elsewhere
- **Health endpoint**: `GET /api/v1/health` with DB connectivity check (200 connected, 503 disconnected)

## Tech Stack Quick Reference

| Layer | Choice |
|-------|--------|
| Frontend | React 18, TypeScript, Vite, Ant Design 5.x, Zustand, Axios + React Query, ECharts, MSW |
| Backend | Python 3.10, FastAPI, SQLAlchemy 2.0, Alembic, OAuth2+JWT |
| ML | PyTorch 2.x, torchvision, ONNX Runtime 1.18+ |
| Agent | LiteLLM (OpenAI-compatible API) |
| DB | PostgreSQL 15 (SQLite for dev) |
| Deploy | Docker Compose |
| Testing | Vitest (FE), pytest + factory_boy (BE) |

## Team Roles (9 people)

- P1: 夏镜萧 — Tech Lead / Architect — API contract, Agent engine, BE code review, integration, training engine (补位 P8)
- P2: 蔡宇 — FE Lead — scaffold, routing, Zustand, component library, FE code review
- P3: 倪义凡 — FE Dev — data management + cleaning/EDA pages
- P4: 叶万琴 — FE Dev — model building + training monitoring pages
- P5: 马丹洋 — FE Dev — inference + Agent pages
- P6: 郑浩天 — BE Dev (Infra) — API gateway, auth, project CRUD, DB schema, file storage, config
- P7: 马胤航 — BE Dev (Data) — data upload API, cleaning engine, EDA, augmentation
- P8: 陈钧泽 — BE Dev (Train) — model library API, training engine, WebSocket monitoring
- P9: 于会昌 — QA / DevOps — tests, CI/CD, Docker, GPU environment

Each role's Claude Code prompt is in `prompts/P{n}_*.md`.

## Day 3 Action Items (Critical)

Day 3 is **集成日** — the plan requires P0 full pipeline end-to-end. Auth+Projects are now done, but major gaps remain:

1. **P9 must merge `feat/day2-devops` to main** — CI pipeline + API tests are ready but unmerged
2. **P7 must ship cleaning engine + EDA** — P7 branch is stale and needs rebase; blocks the upload→clean→model pipeline
3. **P3 must ship Cleaning/EDA FE page** — still placeholder
4. **P4 must ship Model building + Training monitoring FE pages** — both still placeholder
5. **P1 must start Agent engine implementation** — Phase 1 (CRUD + tool binding); Phase 2 (SSE chat engine). No `src/agent/` directory exists yet.
6. **P8 must ship real inference engine** — online_inference at minimum; needed for Agent tool wrapping
7. **P9: integration test pass** — CI exists but not yet run on main

If any P0 module is still mock by Day 3 end, apply priority cut order from plan section 6.3.

## Priority Rule

P0 features are non-negotiable and must ship. If time runs out, cut P1 features in the order specified in the plan (section 6.3). P0 includes: upload, cleaning, EDA, CV augmentation, model library, param config, training, monitoring, checkpoint+early stopping, batch inference, online test, model evaluation, Agent dialog + FastAPI tool wrapping + tool binding.
