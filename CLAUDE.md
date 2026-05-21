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

## Current Module Status (Day 3 — as of 2026-05-21)

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
- ✅ Auth API: real JWT auth (login/register/refresh/me)
- ✅ Projects CRUD: full CRUD with ownership scoping
- ✅ CI pipeline: GitHub Actions lint + integration test + Docker build
- ✅ API integration tests: auth/projects/datasets
- ✅ Cleaning engine: PandasCleaningEngine (5 operations) — merged PR #25
- ✅ EDA service: PandasEdaService + visualization data — merged PR #25
- ✅ Augmentation: PillowAugmentationService (CV image transforms) — merged PR #25
- ✅ P3 FE: Cleaning/EDA/Augment pages with real components (CleaningOperationsTab, EdaReportTab, AugmentationTab) — merged PR #27
- ✅ P4 FE: Training monitoring page (626 lines, 3-tab: jobs/create/monitor + ECharts) — merged PR #28
- ✅ P1 Agent engine: full implementation (9 files, 12 endpoints, SSE chat, tool binding) — merged PR #26

**Day 3 (集成日) — in progress**
- ✅ P6 Auth+Projects API shipped
- ✅ P7 cleaning/EDA/augmentation real engines shipped
- ✅ P1 Agent engine implementation shipped (CRUD + tool binding + SSE chat + prompts)
- ✅ P3 FE Cleaning/EDA pages with real components
- ✅ P4 FE Training monitoring page with Mock WebSocket metrics
- ✅ P4 review fixes: dataset API, gauge chart layout, unwrap dedup — merged PR #31
- ❌ P8 inference engine: still mock
- ❌ P5 Agent chat workspace: PR #29 open (`feat/p5-day3-agent-chat`)
- ❌ P9 Day 3 tests: PR #30 open (`feat/day3-devops`) — cleaning/EDA tests + E2E flow test
- ❌ FE ↔ BE real API integration (most FE pages still use MSW mock)
- ❌ Agent ↔ Inference tool call end-to-end

### Backend (merged to main)

| Module | Path | Status | Gap |
|--------|------|--------|-----|
| Dataset upload/CRUD | `src/app/api/v1/datasets/` | ✅ Real (UploadService + DatasetService + PandasDataParser) | — |
| Data cleaning | `src/app/api/v1/cleaning/` | ✅ Real (PandasCleaningEngine: missing/outlier/dedup/encode/type-convert) | — |
| EDA | `src/app/api/v1/eda/` | ✅ Real (PandasEdaService: stats + visualizations) | — |
| Augmentation | `src/app/api/v1/eda/` | ✅ Real (PillowAugmentationService: CV image transforms) | — |
| Inference | `src/app/api/v1/inference/` | ❌ Mock (5 endpoints return hardcoded data) | P8 — no real inference yet |
| Training jobs | `src/app/api/v1/training/` | ✅ Real (PyTorch subprocess + state machine + checkpoint + early stopping) | — |
| Model library | `src/app/api/v1/models/` | ✅ Real (SQLAlchemy CRUD + 6 architectures) | — |
| Experiments | `src/app/api/v1/experiments/` | ✅ Real (CRUD + comparison + auto-create) | — |
| WebSocket | `src/app/api/v1/ws/` | ✅ Real (status-file polling + diff-based push) | — |
| Auth | `src/app/api/v1/auth/` | ✅ Real (JWT login/register/refresh/me + bcrypt) | — |
| Projects | `src/app/api/v1/projects/` | ✅ Real (CRUD + ownership scoping + pagination) | — |
| Agent | `src/agent/` | ✅ Real (CRUD + tool binding + SSE chat + prompts, 12 endpoints) | MockLLM default; needs real inference for tool calls |

### DevOps & Testing

| Item | Path | Status |
|------|------|--------|
| CI pipeline | `.github/workflows/ci.yml` | ✅ lint + integration-test + Docker build (merged) |
| Auth API tests | `backend/tests/api/test_auth.py` | ✅ 197 lines |
| Projects API tests | `backend/tests/api/test_projects.py` | ✅ 221 lines |
| Datasets API tests | `backend/tests/api/test_datasets.py` | ✅ 345 lines |
| Test factories | `backend/tests/factories/` | ✅ user/project/dataset factories |
| Day 3 tests (PR #30) | `backend/tests/api/test_cleaning_eda.py` + `test_training.py` + `test_e2e_flow.py` | ❌ Open PR, not yet merged |

### Frontend (merged to main)

| Page | Path | Status | Gap |
|------|------|--------|-----|
| Dashboard | `DashboardPage.tsx` | ✅ Complete | — |
| Login/Register | `LoginPage.tsx` / `RegisterPage.tsx` | ✅ Complete | — |
| Data management | `ProjectDataPage.tsx` + `DataManagementView.tsx` | ✅ Upload + list + preview (290-line component) | — |
| Cleaning & EDA | `ProjectCleaningPage.tsx` + P3 components | ✅ 3 tabs with real UI (CleaningOperationsTab 360行, EdaReportTab 155行, AugmentationTab 202行) | — |
| Model building | `ProjectModelsPage.tsx` | ✅ 501 lines, CRUD + param config + architecture select | — |
| Training monitoring | `ProjectTrainingPage.tsx` | ✅ 615 lines, 3-tab (jobs/create/monitor) + ECharts + Mock WS metrics | Day 3: switch to real WebSocket |
| Inference testing | `ProjectInferencePage.tsx` | ✅ 556 lines, evaluation + online test + batch + confusion matrix | — |
| Agent management | `ProjectAgentsPage.tsx` | ✅ 400 lines, dialog + tool binding UI | PR #29: Agent chat workspace |

**Note**: P2 frontend PR #23 added CodeEditor, CommonModal, MSW handlers (models/training/experiments), Ant Design theme, and FileUpload chunk upload. These are on main.

### Feature Completion Summary

**Backend (10/11 done)**
- ✅ Dataset upload/CRUD (UploadService + PandasDataParser)
- ✅ Data cleaning (PandasCleaningEngine: 5 operations)
- ✅ EDA (PandasEdaService: stats + visualizations)
- ✅ Augmentation (PillowAugmentationService: CV image transforms)
- ✅ Training jobs (subprocess + state machine + checkpoint + early stopping)
- ✅ Model library (6 architectures)
- ✅ Experiments (CRUD + comparison + auto-create)
- ✅ WebSocket (status-file polling + diff-based push)
- ✅ Auth (JWT login/register/refresh/me)
- ✅ Projects (CRUD + ownership scoping)
- ✅ Agent (CRUD + tool binding + SSE chat + prompts, MockLLM default)
- ❌ Inference (still mock — 5 endpoints return hardcoded data)

**Frontend (8/8 pages have real UI)**
- ✅ Dashboard
- ✅ Login/Register
- ✅ Data management (DataManagementView 290行)
- ✅ Cleaning & EDA (3 components: CleaningOperationsTab, EdaReportTab, AugmentationTab)
- ✅ Model building (501行, CRUD + param config)
- ✅ Training monitoring (615行, 3-tab + ECharts + Mock WS metrics)
- ✅ Inference testing (556行, evaluation + online test + batch)
- ✅ Agent management (400行, dialog + tool binding; PR #29 adds chat workspace)

### Key Blockers

1. **P8 (Inference)**: Still mock. Needed for Agent tool call end-to-end. Blocks the upload→clean→model→train→infer full pipeline and Agent tool wrapping.
2. **FE ↔ BE real API integration**: Most FE pages still use MSW handlers; Day 3 requires switching to real backend APIs.
3. **Agent chat end-to-end**: PR #29 adds chat workspace UI, but Agent tool calls still route to MockLLM and mock inference. Needs real inference engine (P8) for actual tool execution.
4. **P9 Day 3 tests**: PR #30 open but not merged — cleaning/EDA API tests + training API tests + E2E flow test.
5. **WebSocket real integration**: Training monitor uses Mock WS (`useTrainingMetricsMock`); needs switch to real WebSocket endpoint.

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
│       │   ├── agent.py
│       │   ├── agent_tool.py
│       │   ├── conversation.py
│       │   ├── chat_message.py
│       │   └── prompt_template.py
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
├── agent/                   # Agent engine (P1 — implemented)
│   ├── router.py            #   12 API endpoints (CRUD + tools + chat + prompts)
│   ├── service.py           #   Agent business logic + tool binding + conversation management
│   ├── chat_engine.py       #   SSE streaming + tool-call loop + message persistence
│   ├── tool_wrapper.py      #   Model → OpenAI function-calling schema + tool execution
│   ├── llm_provider.py      #   LiteLLMProvider + MockLLMProvider
│   ├── prompt_manager.py    #   Template CRUD + $variable rendering
│   ├── repository.py        #   DB queries for Agent/AgentTool/Conversation/ChatMessage/PromptTemplate
│   └── schemas.py           #   Pydantic request/response models
frontend/
├── src/
│   ├── pages/               # React page components
│   ├── api/                 # Axios API wrappers + generated types
│   ├── mocks/               # MSW handlers per module
│   └── lib/                 # Axios instance, Zustand stores
```

## API Contract

The single source of truth is `docs/api/openapi.yaml` (maintained by P1/Tech Lead), frozen on Day 1. All endpoints use prefix `/api/v1`. Responses follow `{code, message, data, request_id}`. Pagination is `{page, page_size, total, items[]}`. Errors use 8-digit codes `XX-YY-ZZZ` (module + category + sequence). Auth via `Authorization: Bearer <JWT>`.

Current route count: **78 registered endpoints** (74 REST + 1 WebSocket + 3 internal) across auth, projects, datasets, cleaning, EDA, inference, training, models, experiments, agents, WebSocket, and health. Agent module adds 12 endpoints.

## Error Code Modules

| Module | XX | Key Codes |
|--------|-----|-----------|
| Auth | 10 | ERR_AUTH_MISSING (10-3-1), ERR_AUTH_INVALID (10-3-2), ERR_AUTH_USERNAME_EXISTS (10-4-1) |
| Project | 20 | ERR_PROJECT_NOT_FOUND (20-2-1), ERR_PROJECT_FORBIDDEN (20-3-1) |
| Dataset | 30 | ERR_DATASET_NOT_FOUND (30-2-1), ERR_UPLOAD_INCOMPLETE (30-4-1) |
| Model | 40 | ERR_MODEL_NOT_FOUND (40-2-1) |
| Training | 50 | ERR_TRAINING_JOB_NOT_FOUND (50-2-1), ERR_TRAINING_INVALID_TRANSITION (50-1-1) |
| Inference | 60 | ERR_INFERENCE_TASK_NOT_FOUND (60-2-1) |
| Agent | 70 | ERR_AGENT_NOT_FOUND (70-2-1), ERR_AGENT_INVALID_STATUS (70-1-1), ERR_AGENT_FORBIDDEN (70-3-1), ERR_AGENT_TOOL_BIND_FAILED (70-4-1), ERR_AGENT_CHAT_FAILED (70-5-1), ERR_AGENT_TOOL_ROUND_LIMIT (70-5-2), ERR_AGENT_PROMPT_RENDER_FAILED (70-6-1) |
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

All settings live in **`src/infra/config.py`** (canonical source). `src/app/core/config.py` only re-exports `settings` from infra. Key fields: `database_url`, `storage_root`, `jwt_secret_key`, `jwt_algorithm`, `access_token_expire_minutes`, `dev_allow_anonymous`, `mock_mode`, `llm_default_provider` (default "mock"), `llm_default_model`, `llm_api_key`, `llm_api_base`, `agent_max_tool_rounds` (default 5), `agent_max_history_messages` (default 50).

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

Day 3 is **集成日** — the plan requires P0 full pipeline end-to-end. Backend is 10/11 done; FE all 8 pages have real UI. Remaining work:

1. **P8 must ship real inference engine** — online_inference at minimum; needed for Agent tool call end-to-end and the full pipeline
2. **Review and merge PR #29** (`feat/p5-day3-agent-chat`) — Agent chat workspace UI
3. **Review and merge PR #30** (`feat/day3-devops`) — Day 3 API tests + E2E flow test
4. **FE ↔ BE real API switch** — Most FE pages still use MSW mock; need to verify against real backend
5. **Training monitor WebSocket switch** — Replace `useTrainingMetricsMock` with real WebSocket connection
6. **Agent ↔ Inference end-to-end** — Agent tool calls currently use mock; needs real inference (P8) for actual execution
7. **Alembic migration for Agent models** — Agent/AgentTool/Conversation/ChatMessage/PromptTemplate tables need migration file

If any P0 module is still mock by Day 3 end, apply priority cut order from plan section 6.3.

## Priority Rule

P0 features are non-negotiable and must ship. If time runs out, cut P1 features in the order specified in the plan (section 6.3). P0 includes: upload, cleaning, EDA, CV augmentation, model library, param config, training, monitoring, checkpoint+early stopping, batch inference, online test, model evaluation, Agent dialog + FastAPI tool wrapping + tool binding.
