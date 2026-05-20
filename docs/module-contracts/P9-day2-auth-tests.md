# Module Contract — P9 Day 2 Part 2 (Auth 集成测试)

**Owner**: P9 于会昌  
**Branch**: `feat/day2-devops`  
**Scope**: Auth API 集成测试 + 测试脚手架接入 FastAPI

## 交付物

| # | 内容 | 状态 |
|---|------|------|
| 1 | `backend/tests/api/test_auth.py` | ✅ 11 用例 |
| 2 | `backend/tests/factories/user.py` | ✅ UserFactory |
| 3 | `backend/tests/conftest.py` | ✅ TestClient + SQLite 内存库 |
| 4 | Auth API 最小实现（P6 未落地前的测试依赖） | ✅ 见下表 |

> 说明：原仓库无 `/api/v1/auth/*` 实现，为使集成测试可运行，在 `src/app` 补充了与 OpenAPI 对齐的最小 Auth 模块（login / register / refresh / me）。P6 可在后续 PR 中扩展，测试契约保持不变。

## 测试用例覆盖

| 端点 | 正常流程 | 异常流程 |
|------|----------|----------|
| `POST /auth/register` | 注册成功 → 201 + User | 重复用户名 → 400；密码过短 → 400 |
| `POST /auth/login` | 登录成功 → TokenPair | 密码错误 / 用户不存在 → 401 |
| `POST /auth/refresh` | 刷新成功 → 新 TokenPair | 无效 refresh_token → 401 |
| `GET /auth/me` | Bearer 有效 → User | 无 Token / 无效 Token → 401 |

所有成功/失败响应均断言 `{code, message, data, request_id}` 结构。

## 文件清单

### 测试（P9 主交付）

| 文件 | 说明 |
|------|------|
| `backend/tests/api/test_auth.py` | Auth 集成测试 |
| `backend/tests/api/__init__.py` | 包标记 |
| `backend/tests/factories/user.py` | factory_boy `UserFactory` |
| `backend/tests/factories/__init__.py` | 导出 UserFactory |
| `backend/tests/conftest.py` | `api_client`、`db_session`、双 Base 元数据 |
| `backend/pytest.ini` | `pythonpath` 增加项目根目录 |

### Auth 实现（支撑测试，供 P6 接续）

| 文件 | 说明 |
|------|------|
| `src/app/api/v1/auth/router.py` | 四个 Auth 路由 |
| `src/app/api/v1/auth/__init__.py` | 路由导出 |
| `src/app/services/auth_service.py` | 注册/登录/刷新/查用户 |
| `src/app/schemas/auth.py` | Pydantic 模型 |
| `src/app/core/security.py` | bcrypt + JWT |
| `src/app/core/config.py` | `jwt_secret_key` / `jwt_algorithm` |
| `src/app/core/errors.py` | `ERR_AUTH_DUPLICATE_USER` |
| `src/app/api/deps.py` | JWT `get_current_user` |
| `src/app/api/v1/router.py` | 挂载 auth 路由 |

### CI

| 文件 | 说明 |
|------|------|
| `.github/workflows/ci.yml` | integration-test 增加 Auth 测试环境变量 |

## 本地运行

```bash
cd backend
export DATABASE_URL=sqlite://          # Windows: $env:DATABASE_URL="sqlite://"
export DEV_ALLOW_ANONYMOUS=false
export JWT_SECRET_KEY=test-jwt-secret-key-32chars-minimum
pip install -r ../requirements.txt
pytest tests/api/test_auth.py -v
```

## Commit 建议

```
feat(devops): add Auth API integration tests with UserFactory

- backend/tests/api/test_auth.py: login, register, refresh, me
- Wire TestClient + SQLite in-memory in conftest
- Minimal P6-aligned auth routes for test execution
```

可选拆分：

1. `feat(infra): implement minimal auth API (login/register/refresh/me)`
2. `test(devops): add auth integration tests and UserFactory`
