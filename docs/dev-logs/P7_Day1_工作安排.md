# P7 Day1 工作安排：数据 API 地基 + 分片上传

> 日期：2026-05-19  
> 角色：P7 BE Dev（数据层 API + 清洗引擎）  
> 分支：`feature/p7`（建议 PR 合并目标：`develop` / `main` 按 P1 当日通知）  
> 契约：`docs/api/openapi.yaml`、`src/shared/protocols.py`

---

## 一、Day1 目标（对照实施计划）

| 检查点 | 计划要求 | P7 交付物 |
|--------|----------|-----------|
| **10:00 M1-A** | 契约冻结 | 已具备：OpenAPI 数据集路径 + `protocols.py` 中 P7 Protocol |
| **12:00 CP2** | Router 骨架 + Mock handler | ✅ 已在本地 `hezuo01/backend/` 完成，待迁入 monorepo |
| **14:00** | 数据上传 API（不含清洗） | 分片上传 init → chunk → complete **真实文件流**（可先 SQLite/文件系统，不等 P6 DB） |
| **18:00 CP3** | `/docs` 可访问、curl 有响应 | P7 路由在 monorepo 可启动；上传链路可用 Postman/curl 走通 |
| **18:00+ 可选** | 清洗引擎骨架 | 仅目录 + `CleaningProtocol` 空实现 / 委托 Mock，**不抢 Day2 主任务** |

**Day1 不做**：缺失值/异常值/去重真实计算（Day2）、EDA 图表计算（Day2）、推理真实引擎（P8）。

---

## 二、当前基线（检索结论）

| 项 | 状态 |
|----|------|
| 本地原型 `hezuo01/backend/` | 27 端点 Mock，可 `uvicorn` 独立运行 |
| `deepflow` 分支 `feature/p7` | 已创建，**尚无 P7 commit** |
| `deepflow` 内 `backend/` | main 上不存在；P6 在 `origin/feat/p6-backend-main`（`backend/main.py` 单文件骨架） |
| 前端 P3 | MSW `datasets.ts` 已有，下午可对 P7 真实 `:8000` 或团队统一后端 |
| 阻塞项 | P6 JWT/RBAC/DDL 未进 main → P7 用 `MockStorage` + 本地 SQLite 降级，Day3 再替换 |

---

## 三、时间块安排

### 09:00–10:00｜站会 + 对齐（CP1）

- [ ] 确认 P1：`openapi.yaml` / `contract-v1` tag 是否已打
- [ ] 确认 P6：`feat/p6-backend-main` 何时合入 develop；`backend/` 目录约定
- [ ] 确认 P3：上传页下午联调端口（8000 或统一网关）
- [ ] 与 P8 确认：推理 5 端点是否全部由 P7 先 Mock（当前方案：是）

### 10:00–12:00｜迁入 monorepo + Mock 合入（CP2 收尾）

**目标**：团队仓库内可 `git clone` 后直接跑 P7 Swagger。

| # | 任务 | 产出 |
|---|------|------|
| 1 | `cd deepflow && git checkout feature/p7 && git pull origin main` | 分支最新 |
| 2 | 将 `hezuo01/backend/` 调整为 monorepo 结构（见下方目录约定） | `backend/` 或 `backend/src/app/` |
| 3 | `requirements.txt` 与 P6 依赖对齐（先最小集：fastapi, uvicorn, pydantic-settings, python-multipart） | 可安装 |
| 4 | 实现 `MockFileStorage`（实现 `StorageProtocol` 中 upload/dataset 路径） | `backend/app/services/storage_mock.py` |
| 5 | `commit` + `push origin feature/p7` | 远程可见 |
| 6 | 本地验证：`GET /health`、`GET /api/v1/projects/{id}/datasets` | 截图/日志备查 |

**建议目录（与 P6 单文件 `main.py` 并存阶段）**：

```
deepflow/
├── backend/
│   ├── requirements.txt
│   ├── main.py                 # 入口：挂载 P7 api_router + /health
│   └── app/
│       ├── api/v1/             # datasets / cleaning / eda / inference routers
│       ├── core/
│       ├── schemas/
│       ├── mock/
│       └── services/           # storage_mock.py, upload_service.py（下午）
├── src/shared/protocols.py     # 只读依赖，不修改
└── docs/dev-logs/P7_Day1_工作安排.md
```

### 12:00–12:30｜午间集成（CP2）

- [ ] 在群里发 Swagger 地址 + 示例 `project_id` / `dataset` 列表 curl
- [ ] 请 P3 用 MSW 或直连后端验证列表/详情字段是否与 `openapi.yaml` 一致
- [ ] 记录与契约不一致项 → 提 Issue 或 @P1

### 14:00–17:30｜分片上传真实实现（Day1 核心）

**范围**：仅上传三件套 + 合并后写 `raw/` + 写内存/SQLite 数据集元数据；**清洗仍 Mock**。

| 端点 | 实现要点 |
|------|----------|
| `POST .../upload/init` | 生成 `upload_id`；`{STORAGE_ROOT}/uploads/{upload_id}/`；返回 `expires_at` |
| `POST .../upload/{uid}/chunk` | 按 OpenAPI：`multipart` + `chunk_index` + `total_chunks`；可选兼容 `Content-Range` |
| `POST .../upload/{uid}/complete` | 合并分片 → 检测格式（csv/json/parquet 先支持 csv）→ `columns_meta` / `num_samples` → 移到 `projects/{pid}/datasets/{ds_id}/raw/` |

| # | 子任务 | 验收 |
|---|--------|------|
| 1 | `UploadService`：写分片、合并、校验大小 | 单元测试或脚本上传 2MB 文件 |
| 2 | `DataParser` 最小实现：CSV 解析前 100 行 preview 元数据 | complete 后 `num_samples` > 0 |
| 3 | 数据集记录：Day1 用 SQLite `datasets` 表（与 P6 DDL 字段对齐）或 JSON 文件降级 | GET detail 返回真实 path |
| 4 | 错误码 `30-01-xxx` / `30-02-xxx` 参数错误、资源不存在 | 非法 upload_id 返回约定格式 |

### 17:30–18:00｜CP3 验收准备

- [ ] `http://localhost:8000/docs` 含 Datasets 全部路径
- [ ] curl 脚本（保存在 `backend/scripts/test_upload.sh` 或 `.ps1`）：
  - init → 2 个 chunk → complete → GET datasets → GET preview
- [ ] 更新本日志「完成内容」小节
- [ ] `git commit` + `push`；如需 PR：`feat(data): day1 mock routers and chunked upload`

### 18:00–22:00｜可选冲刺

- [ ] `cleaning/` 下抽出 `MockCleaningService`，路由改为调用 Service 接口（为 Day2 换真实现做准备）
- [ ] 阅读 P6 `feat/p6-backend-main` 的 `main.py`，列出 Day3 挂载点清单

---

## 四、协作接口

| 角色 | Day1 需要对方提供 | P7 提供给对方 |
|------|-------------------|---------------|
| **P6** | 最终 `backend` 目录、鉴权 Depends 名称 | Mock 阶段可先不带 JWT；文档说明 Header 可选 |
| **P3** | 上传页 UI 字段名、进度回调方式 | Swagger + 示例 project_id + upload curl |
| **P1** | 契约变更通知 | 不符合 openapi 的字段清单 |
| **P8** | 无 | 推理 5 端点 Mock 保持可用 |
| **P9** | 无 | 晚间可提供 `docker compose` 所需启动命令 |

---

## 五、代码质量五项检查（每次提交前）

| 维度 | 要求 | 实现位置 |
|------|------|----------|
| **OpenAPI 契约** | 路径、`UploadInitRequest.total_size/total_chunks`、`Dataset.columns_meta` 数组、`CleaningResult` 字段 | `schemas/`、`api/v1/*/router.py` |
| **Protocol DI** | 存储/清洗通过 `Depends(get_storage)` 注入，禁止 router 内 `new MockStore()` | `api/deps.py`、`services/*` |
| **DDL 一致** | ORM 仅含 `datasets` 表 DDL 字段；API 层补充 `num_columns`/`size_bytes` | `db/models.py`、`mappers/dataset_mapper.py` |
| **安全** | ORM 参数化查询；`dev_allow_anonymous=False` 时强制 Bearer；校验 `project_id` 归属 | `repositories/`、`deps.get_current_user_id` |
| **错误码** | 8 位整数 `30002001` 等，统一 `AppError` + 全局 handler | `core/errors.py`、`core/exception_handlers.py` |

## 六、验收清单（Day1 结束前自查）

```
[ ] feature/p7 已 push，含 backend 代码
[ ] 所有 P7 路径在 Swagger 可见（Mock 或真实均可）
[ ] 分片上传 E2E：init → chunk×N → complete → 数据集可查
[ ] 响应格式统一：{ code, message, data, request_id }
[ ] 未在 main 上直接开发；未 force push
[ ] dev-log 已更新「完成内容」与「阻塞项」
```

---

## 七、风险与预案

| 风险 | 预案 |
|------|------|
| P6 分支未合并，无统一入口 | P7 独立 `backend/main.py` 启动，Day3 再 `include_router` |
| 与 openapi chunk 字段不一致 | 以 `openapi.yaml` 为准；`Content-Range` 作兼容 |
| 本机无法 push GitHub | 先本地 commit，网络恢复后 push；阻塞项同步 P1 |
| 下午上传来不及 | 保证 init+chunk 落盘，complete 可仍返回 Mock 元数据，Day2 上午补齐解析 |

---

## 八、完成内容（待填写）

_18:00 站会后由 P7 填写_

- 

## 九、阻塞项（待填写）

- 
