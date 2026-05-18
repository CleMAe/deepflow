# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DeepFlow** is an end-to-end deep learning platform targeting business developers. The core pipeline is: Data Upload → Data Cleaning → Model Building → Training → Inference → Agent Construction. The authoritative plan is `DeepFlow_实施计划_V1.0_DSv4OC.md`; the PRD is `DeepFlow_PRD_V1.0.md`.

## Architecture

Four-layer architecture with strict decoupling:

- **Interaction Layer (Frontend)**: React 18 + TypeScript + Vite, Ant Design 5.x, Zustand, ECharts, MSW for mock
- **Service Layer (Backend API)**: Python 3.10 + FastAPI, SQLAlchemy 2.0 + Alembic, PostgreSQL 15 (SQLite for dev)
- **Engine Layer (Core)**: PyTorch 2.x training engine (runs as subprocess, isolated from API process), ONNX Runtime inference, Agent engine (OpenAI-compatible via LiteLLM)
- **Data Layer**: PostgreSQL for metadata, local filesystem for files/models (no S3/MinIO in V1.0), UUID-based directory structure

Key decoupling: all inter-module communication via REST API (no in-process function calls). Real-time monitoring via WebSocket push (no polling). Large files shared via filesystem UUID paths, not API transfer.

## API Contract

The single source of truth is `openapi.yaml` (maintained by P1/Tech Lead), frozen on Day 1. All endpoints use prefix `/api/v1`. Responses follow `{code, message, data, request_id}`. Pagination is `{page, page_size, total, items[]}`. Errors use 8-digit codes `XX-YY-ZZZ` (module + category + sequence). Auth via `Authorization: Bearer <JWT>`.

See `DeepFlow_实施计划_V1.0_DSv4OC.md` section 4.1 and 7 for the full 50+ endpoint list.

## Git Workflow

Branch strategy:
- `main` — production-ready, no direct push
- `develop` — integration branch, forced merge at 12:00 / 18:00 daily
- `feat/<module>` — feature branches, lifespan ≤ 1 day

Branch naming: `feature/<module>-<owner>-<short-task>` or `fix/<module>-<owner>-<short-task>`

PR rules: at least 1 reviewer approve; P1 reviews all BE PRs, P2 reviews all FE PRs. Commit format: `feat(module): description` / `fix(module): description` / `docs: description`.

No code may sit unpushed for more than 2 hours.

## Key Protocols and Conventions

- **Shared interfaces**: Python Protocol classes in `src/shared/protocols.py` (frozen Day 1 10:00)
- **File storage layout**: `{STORAGE_ROOT}/projects/{project_uuid}/datasets|models|experiments/...`
- **WebSocket training messages**: JSON with `type` (metrics/log/alert/status_change/progress) + `data`
- **Training engine**: runs as subprocess; state machine with enum + DB transaction consistency
- **Async task states**: `pending / running / success / failed / cancelled / paused`
- **Mock strategy**: FE uses MSW handlers in `@/mocks/handlers/`; BE tests use pytest + factory_boy + SQLite; shared mock server at `scripts/mock_server.py`; synthetic data generator at `scripts/gen_synthetic_data.py`

## Tech Stack Quick Reference

| Layer | Choice |
|-------|--------|
| Frontend | React 18, TypeScript, Vite, Ant Design 5.x, Zustand, Axios + React Query, ECharts, MSW |
| Backend | Python 3.10, FastAPI, SQLAlchemy 2.0, Alembic, OAuth2+JWT |
| ML | PyTorch 2.x, torchvision, ONNX Runtime 1.18+ |
| Agent | LiteLLM (OpenAI-compatible API) |
| DB | PostgreSQL 15 (SQLite for dev) |
| Deploy | Docker Compose |
| Testing | Vitest (FE), pytest (BE) |

## Team Roles (9 people)

- P1: 夏镜萧 — Tech Lead / Architect — API contract, Agent engine, BE code review, integration
- P2: 蔡宇 — FE Lead — scaffold, routing, Zustand, component library, FE code review
- P3: 倪义凡 — FE Dev — data management + cleaning/EDA pages
- P4: 叶万琴 — FE Dev — model building + training monitoring pages
- P5: 马丹洋 — FE Dev — inference + Agent pages
- P6: 郑浩天 — BE Dev (Infra) — API gateway, auth, project CRUD, DB schema, file storage
- P7: 马胤航 — BE Dev (Data) — data upload API, cleaning engine, EDA, augmentation
- P8: 陈钧泽 — BE Dev (Train) — model library API, training engine, WebSocket monitoring
- P9: 于会昌 — QA / DevOps — tests, CI/CD, Docker, GPU environment

Each role's Claude Code prompt is in `prompts/P{n}_*.md`.

## Priority Rule

P0 features are non-negotiable and must ship. If time runs out, cut P1 features in the order specified in the plan (section 6.3). P0 includes: upload, cleaning, EDA, CV augmentation, model library, param config, training, monitoring, checkpoint+early stopping, batch inference, online test, model evaluation, Agent dialog + FastAPI tool wrapping + tool binding.
