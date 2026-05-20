# Module Contract — P9 Day 2 (CI/CD Pipeline)

**Owner**: P9 于会昌  
**Date**: Day 2  
**Scope**: GitHub Actions CI（仅 Pipeline，不含 deploy）

## 交付物

| # | 任务 | 状态 |
|---|------|------|
| 1 | `.github/workflows/ci.yml` | ✅ |

## 创建 / 修改的文件

| 文件 | 说明 |
|------|------|
| `.github/workflows/ci.yml` | 主 CI 工作流 |
| `docs/module-contracts/P9-day2-ci.md` | 本契约文件 |

## Pipeline 设计

### 触发条件

- `push` → `main` / `develop`
- `pull_request` → `main` / `develop`
- 同 ref 并发时取消进行中的旧运行（`concurrency`）

### Job 顺序（严格串行）

```
lint → unit-test → integration-test → build-docker
```

| Job | 内容 |
|-----|------|
| **lint** | 前端 `npm run lint`（ESLint）；后端 `ruff --select E9,F63,F7,F82` + `compileall` |
| **unit-test** | 前端 `npm test`（Vitest） |
| **integration-test** | `backend/` 下 `pytest -m "not integration and not gpu"`，使用 Day 1 SQLite 内存 fixtures |
| **build-docker** | 构建 `docker/backend`、`docker/frontend` 镜像，`push: false`，`docker image inspect` 校验 |

### 环境

| 项 | 值 |
|----|-----|
| Python | 3.10 |
| Node | 20 |
| 后端依赖 | 根目录 `requirements.txt` |
| 测试 DB | `sqlite+aiosqlite:///:memory:`（conftest 内存库为主） |

### build-docker 说明

- **不 push** 到镜像仓库
- **不构建** `gpu-train`（PyTorch/CUDA 镜像体积大，Day 2 仅验证 app 镜像）
- CI 步骤内 `cp requirements.txt backend/requirements.txt`，兼容现有 `docker/backend/Dockerfile` 路径（未改 Dockerfile）

## 本地对齐命令

```bash
# lint
cd frontend && npm ci && npm run lint
pip install -r requirements.txt ruff
ruff check src backend
python -m compileall -q src backend

# unit-test
cd frontend && npm test

# integration-test
pip install -r requirements.txt
cd backend && pytest -m "not integration and not gpu"

# build-docker（需 Docker）
cp requirements.txt backend/requirements.txt
docker build -f docker/backend/Dockerfile -t deepflow-backend:local .
docker build -f docker/frontend/Dockerfile -t deepflow-frontend:local .
```

## 未包含（后续 Day）

- `deploy` job / 环境发布
- `gpu-train` 镜像 CI 构建
- GitHub Actions 密钥与云端 registry push
- 覆盖率门禁、E2E 测试

## Commit 建议

```
feat(devops): add GitHub Actions CI pipeline (lint → test → docker build)
```
