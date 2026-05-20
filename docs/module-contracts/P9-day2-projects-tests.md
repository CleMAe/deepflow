# Module Contract — P9 Day 2 Part 3 (Project 集成测试)

**Owner**: P9 于会昌  
**Branch**: `feat/day2-devops`  
**Scope**: Project CRUD 集成测试 + 最小 API 实现

## 交付物

| # | 内容 | 状态 |
|---|------|------|
| 1 | `backend/tests/api/test_projects.py` | ✅ 14 用例 |
| 2 | `backend/tests/factories/project.py` | ✅ ProjectFactory |
| 3 | `backend/tests/api/conftest.py` | ✅ `auth_user` / `auth_headers` |
| 4 | Project API 最小实现 | ✅ 见下表 |

## 测试覆盖

| 端点 | 正常 | 异常 |
|------|------|------|
| `GET /projects` | 分页列表 | 无 Token → 401 |
| `POST /projects` | 201 创建 | 无 Token → 401 |
| `GET /projects/{id}` | 详情 | 404 / 401 / 403（非 owner） |
| `PUT /projects/{id}` | 更新 | 404 |
| `DELETE /projects/{id}` | 删除后 404 | 404 / 401 |

所有响应断言 `{code, message, data, request_id}`；请求均带 `Authorization: Bearer <token>`（除 401 用例）。

## 文件清单

### 测试

| 文件 | 说明 |
|------|------|
| `backend/tests/api/test_projects.py` | Project 集成测试 |
| `backend/tests/api/conftest.py` | 鉴权 fixtures |
| `backend/tests/factories/project.py` | ProjectFactory |
| `backend/tests/factories/__init__.py` | 导出 ProjectFactory |
| `backend/tests/conftest.py` | 仅增加 ProjectFactory session 绑定与 fixture（未改引擎配置） |

### 实现（支撑测试）

| 文件 | 说明 |
|------|------|
| `src/app/api/v1/projects/router.py` | 5 个 CRUD 路由 |
| `src/app/services/project_service.py` | 业务逻辑 + owner RBAC |
| `src/app/schemas/project.py` | Pydantic 模型 |
| `src/app/api/v1/router.py` | 挂载 projects 路由 |
| `src/app/core/errors.py` | `ERR_PROJECT_NOT_FOUND` / `ERR_PROJECT_FORBIDDEN` (模块 20) |

## 本地运行

```bash
cd backend
pytest tests/api/test_projects.py -v
pytest tests/api/test_auth.py tests/api/test_projects.py -v
```

## Commit 建议

```
test(devops): add Project API integration tests with ProjectFactory

- CRUD tests for /api/v1/projects with Bearer auth
- ProjectFactory + auth_headers fixtures
- Minimal projects router/service aligned with OpenAPI
```
