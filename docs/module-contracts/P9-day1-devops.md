# Module Contract — P9 Day 1 (QA / DevOps)

**Owner**: P9 于会昌  
**Date**: Day 1  
**Scope**: 测试脚手架、合成数据、Docker Compose 初版、GPU 验证

## 交付物

| # | 任务 | 状态 |
|---|------|------|
| 1 | 后端 pytest + factory_boy + SQLite 内存库 | ✅ |
| 2 | 前端 Vitest 基础配置 | ✅ |
| 3 | `scripts/gen_synthetic_data.py` | ✅ |
| 4 | `docker-compose.yml` + 服务 Dockerfile | ✅ |
| 5 | GPU 验证脚本与文档 | ✅ |

## 创建 / 修改的文件

### 根目录

| 文件 | 说明 |
|------|------|
| `.gitignore` | Python / Node / 数据目录忽略规则 |
| `.env.example` | Compose 环境变量模板 |
| `docker-compose.yml` | `db` + `backend` + `frontend` + `gpu-train`（profile: gpu） |

### 后端测试 (`backend/`)

| 文件 | 说明 |
|------|------|
| `backend/requirements.txt` | 运行时依赖占位（P6 扩展） |
| `backend/requirements-dev.txt` | pytest、factory_boy、httpx 等 |
| `backend/pytest.ini` | pytest 全局配置与 markers |
| `backend/tests/conftest.py` | SQLite 内存库 + 事务回滚 fixtures |
| `backend/tests/test_smoke.py` | 脚手架冒烟测试 |
| `backend/tests/support/models.py` | 临时 ORM 模型（P6 接入后替换） |
| `backend/tests/factories/base.py` | factory_boy 工厂基类 |

### 前端测试 (`frontend/`)

| 文件 | 说明 |
|------|------|
| `frontend/package.json` | Vitest / Testing Library 脚本与依赖 |
| `frontend/tsconfig.json` | TS 配置（含 `@/*` 别名） |
| `frontend/vitest.config.ts` | Vitest + jsdom + setupFiles |
| `frontend/src/test/setup.ts` | jest-dom 扩展 |
| `frontend/src/test/smoke.test.ts` | 运行器冒烟测试 |
| `frontend/src/utils/formatPagination.ts` | 示例工具函数（供 P2 参考测试模式） |
| `frontend/src/utils/formatPagination.test.ts` | 分页逻辑单元测试示例 |

### 脚本与数据

| 文件 | 说明 |
|------|------|
| `scripts/gen_synthetic_data.py` | CSV + 随机图像合成数据 CLI |
| `scripts/requirements-synthetic.txt` | 图像生成依赖（Pillow） |
| `scripts/verify_gpu.sh` | 云端 CUDA / Docker / PyTorch 验证 |

### Docker

| 文件 | 说明 |
|------|------|
| `docker/backend/Dockerfile` | FastAPI 占位镜像 |
| `docker/backend/health_app.py` | `/api/v1/health` 占位端点 |
| `docker/frontend/Dockerfile` | Nginx 静态占位 |
| `docker/frontend/nginx.conf` | 反向代理 `/api` → backend |
| `docker/frontend/index.html` | 占位首页 |
| `docker/gpu-train/Dockerfile` | PyTorch 2.2 + CUDA 12.1 |
| `docker/gpu-train/entrypoint.sh` | CUDA 自检 + idle worker |

### 文档

| 文件 | 说明 |
|------|------|
| `docs/gpu-environment.md` | GPU 环境安装与验证说明 |
| `docs/module-contracts/P9-day1-devops.md` | 本契约文件 |

## 对接说明（给其他角色）

| 角色 | 动作 |
|------|------|
| **P6** | 将 `conftest.py` 中 `api_client` 取消 skip，接入 `app.main` 与 `get_db`；用真实 models 替换 `tests/support/models.py` |
| **P2** | 在现有 `frontend/` 上合并 Vite 脚手架，保留 `vitest.config.ts` 与 `src/test/setup.ts` |
| **P8** | 使用 `python scripts/gen_synthetic_data.py --preset fast-epoch`；将训练引擎挂到 `gpu-train` 服务 |
| **全员** | `docker compose up -d` 启动 db/backend/frontend；GPU 主机执行 `./scripts/verify_gpu.sh` |

## 本地验证命令

```bash
# 后端测试
cd backend && pip install -r requirements-dev.txt && pytest

# 前端测试
cd frontend && npm install && npm test

# 合成数据
pip install -r scripts/requirements-synthetic.txt
python scripts/gen_synthetic_data.py --preset fast-epoch -o data/synthetic

# Compose（无 GPU）
docker compose up -d --build
curl http://localhost:8000/api/v1/health
```

## 基础设施健康端点

`GET /api/v1/health` 是仅供容器健康检查、负载均衡和反向代理使用的基础设施端点。它不进入 `docs/api/openapi.yaml` 的产品 API 契约，但仍遵循 `/api/v1` 前缀，便于 nginx 与其他 API 统一代理。

## 未包含（Day 2+）

- GitHub Actions CI Pipeline
- BE API 集成测试用例
- FE 组件快照测试
- 真实 FastAPI / Vite 生产镜像构建
