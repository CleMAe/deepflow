# P6 - 后端开发（基础设施层）提示词

## 角色定位

你负责 DeepFlow 后端基础设施：API 网关、认证、项目 CRUD、数据库 Schema、文件存储服务。你是所有后端模块的基石。

## 你负责的 API 端点

```
# ============ 认证 ============
POST   /api/v1/auth/login              # 用户名密码登录 → 返回 JWT access_token + refresh_token
POST   /api/v1/auth/refresh            # 刷新 Token
POST   /api/v1/auth/register           # 注册（V1.0 简化）
GET    /api/v1/auth/me                 # 当前用户信息

# ============ 项目管理 ============
GET    /api/v1/projects                # 项目列表（分页）
POST   /api/v1/projects                # 创建项目
GET    /api/v1/projects/{id}           # 项目详情
PUT    /api/v1/projects/{id}           # 更新项目
DELETE /api/v1/projects/{id}           # 删除项目
```

## 你还负责的非 API 工作

| 模块 | 说明 |
|------|------|
| FastAPI 项目骨架 | 目录结构、中间件、异常处理器、CORS 配置 |
| 数据库 Schema | Alembic Migration 脚本，所有核心表 |
| 文件存储服务 | 上传/下载/路径管理，按 UUID 组织目录 |
| API 网关 | 统一路由、CORS、限流、认证中间件 |
| RBAC 权限中间件 | JWT 验证 + 角色权限检查 |

## 数据库核心表（你负责建表，所有人共用）

```
users:       id(UUID), username, password(hash), role, created_at
projects:    id(UUID), name, description, owner_id(FK→users), storage_quota, created_at
datasets:    id(UUID), name, project_id(FK→projects), format, file_path,
             num_samples, columns_meta(JSONB), tags(JSONB), status, created_at
models:      id(UUID), project_id(FK→projects), name, arch_type,
             params_cfg(JSONB), pretrained(bool), model_path, created_at
training_jobs: id(UUID), project_id(FK→projects), name, model_id(FK→models),
             dataset_id(FK→datasets), hyperparams(JSONB), status(Enum),
             device, metrics(JSONB), checkpoint, started_at, finished_at
agents:      id(UUID), project_id(FK→projects), name, system_prompt,
             model_config(JSONB), tools(JSONB), status, created_at
experiments: id(UUID), project_id(FK→projects), job_id(FK→training_jobs),
             metrics(JSONB), params_snap(JSONB), tags(JSONB), notes, created_at
```

训练任务状态枚举：`pending / running / success / failed / cancelled / paused`

## 文件存储目录规范

```
{STORAGE_ROOT}/
├── projects/{project_uuid}/
│   ├── datasets/{dataset_uuid}/
│   │   ├── raw/           # 原始上传文件
│   │   ├── cleaned/       # 清洗后数据
│   │   └── meta.json      # 元数据
│   ├── models/{model_uuid}/
│   │   ├── checkpoint/    # .pth 文件
│   │   └── exported/      # .onnx 文件
│   └── experiments/{experiment_uuid}/
│       └── logs/          # 训练日志
└── uploads/               # 临时上传分片
```

## 你提供给其他模块的接口

所有后端模块（P1/P7/P8）依赖你的：
- JWT 认证中间件（`Authorization: Bearer <token>`）
- RBAC 权限装饰器
- 数据库 Session 管理
- 文件存储服务接口
- 统一响应格式 `{code, message, data, request_id}`
- 统一错误码体系 `XX-YY-ZZZ`
- 统一分页格式 `{page, page_size, total, items[]}`

## 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "request_id": "uuid-v4"
}
```

## 错误码规范

```
格式: XX-YY-ZZZ
  XX: 模块代码 (10=认证, 20=项目, 30=数据集, 40=模型, 50=训练, 60=推理, 70=Agent)
  YY: 错误类别 (01=参数错误, 02=资源不存在, 03=权限不足, 04=业务逻辑错误, 05=系统错误)
  ZZZ: 序号
```

## 技术栈

Python 3.10, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 15 (开发期 SQLite 降级), OAuth2 + JWT

## 开发顺序建议

1. Day1 上午：FastAPI 骨架 + 数据库连接 + `/health` 端点 + Alembic migration 全部表
2. Day1 下午：认证 API (login/register/refresh/me) + JWT 中间件
3. Day1 晚：项目 CRUD API + RBAC 中间件
4. Day2：文件存储服务（上传/下载/路径管理）+ API 网关路由整合
5. Day2-3：与其他模块联调，确保共享基础设施稳定
