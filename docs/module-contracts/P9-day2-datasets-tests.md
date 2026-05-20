# Module Contract — P9 Day 2 Part 4 (Dataset 集成测试)

**Owner**: P9 于会昌  
**Branch**: `feat/day2-devops`  
**Scope**: Dataset CRUD 集成测试 + RBAC 加固

## 交付物

| # | 内容 | 状态 |
|---|------|------|
| 1 | `backend/tests/api/test_datasets.py` | ✅ 16 用例 |
| 2 | `backend/tests/factories/dataset.py` | ✅ DatasetFactory |
| 3 | `require_project_access` RBAC | ✅ 校验 project.owner_id |
| 4 | Dataset 路由 | ✅ 已有实现；`POST` 对齐 201 |

## 测试覆盖

| 端点 | 正常 | 异常 / RBAC |
|------|------|-------------|
| `GET .../datasets` | 分页列表 | 401 / 403（非 owner 项目） |
| `POST .../datasets` | 201 创建元数据 | 401 / 403 |
| `GET .../datasets/{ds_id}` | 详情 | 404 / 403 |
| `PUT .../datasets/{ds_id}` | 更新 | 404 |
| `DELETE .../datasets/{ds_id}` | 删除后 404 | 403 / 404（项目不存在） |

跨项目访问：同一用户访问 A 项目下的 dataset 但 URL 使用 B 项目 ID → **404**（数据集不在该项目作用域内）。

## 文件清单

### 测试

| 文件 | 说明 |
|------|------|
| `backend/tests/api/test_datasets.py` | Dataset 集成测试 |
| `backend/tests/factories/dataset.py` | DatasetFactory（绑定 ProjectFactory） |
| `backend/tests/factories/__init__.py` | 导出 DatasetFactory |
| `backend/tests/conftest.py` | 仅增加 DatasetFactory session 绑定与 fixture（**未改** TestClient / SQLite 引擎） |

### 实现调整

| 文件 | 说明 |
|------|------|
| `src/app/api/deps.py` | `require_project_access` 校验项目归属 |
| `src/app/api/v1/datasets/router.py` | `POST` 返回 201 |

## 本地运行

```bash
cd backend
pytest tests/api/test_datasets.py -v
pytest tests/api/test_auth.py tests/api/test_projects.py tests/api/test_datasets.py -v
```

## Commit 建议

```
test(devops): add Dataset API integration tests with RBAC

- DatasetFactory linked to ProjectFactory
- Enforce project ownership in require_project_access
- Cover list/create/get/update/delete + 401/403/404 cases
```
