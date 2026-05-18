# DeepFlow V1.0 — 4天冲刺实施计划

> **文档性质**：架构师 & Team Lead 项目管理方案  
> **创建日期**：2026-05-18  
> **项目周期**：4天（96小时）  
> **团队规模**：9人  

---

## 目录

1. [架构师全局视角](#1-架构师全局视角)
2. [技术栈与架构决策](#2-技术栈与架构决策)
3. [模块与分工矩阵](#3-模块与分工矩阵)
4. [并行开发协议（关键）](#4-并行开发协议)
5. [4天冲刺时间表](#5-4天冲刺时间表)
6. [风险提示与阻碍预案](#6-风险提示与阻碍预案)
7. [附录：API契约速查](#7-附录api契约速查)

---

## 1. 架构师全局视角

### 1.1 核心策略：契约先行，Mock 驱动，逐日集成

DeepFlow 是一条 **数据 → 清洗 → 模型 → 训练 → 推理 → Agent** 的线性流水线，各模块天然存在上下游依赖。

**并行开发的核心解题思路**：

```
         Day1 上午           Day2              Day3              Day4
         ────────           ────              ────              ────
[契约冻结] + [Mock就绪] → [模块独立开发] → [接口联调] → [端到端集成]
         │                    │                  │                  │
         ├─ API Schema       ├─ 各模块用Mock    ├─ 逐对接真实API   ├─ 全链路回归
         ├─ 数据模型DDL      ├─ 独立可测试      ├─ 消除Mock层      ├─ 性能压测
         ├─ WebSocket协议    └─ 不互相阻塞      └─ 冒烟测试        └─ 交付验收
         └─ 文件存储规范
```

三条铁律：

1. **Day1 10:00前冻结所有接口契约**——任何人必须先对齐契约再写代码。
2. **所有模块自带 Mock**——FE 用 MSW/JSON Server 模拟后端，BE 用脚本注入测试数据，不等人。
3. **每天两次强制集成（12:00 / 18:00）**——任何人的代码必须能在集成环境跑通，不允许“我还在开发中”。

### 1.2 架构分层与模块边界

```
┌──────────────────────────────────────────────────────────────┐
│                     交互层 (Frontend)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Data Mgt │ │Cleaning  │ │Model Bld │ │Train/Inf │ Agent   │
│  │   Pages  │ │  Pages   │ │  Pages   │ │  Pages   │  Pages  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘───┬─────┘
│       │             │            │            │          │
│       └─────────────┴────────────┴────────────┴──────────┘
│                           │ HTTP REST + WebSocket
│                    ┌──────┴──────┐
│                    │  API Gateway│ (Auth, Routing, Rate Limit)
│                    └──────┬──────┘
├───────────────────────────┼──────────────────────────────────┤
│                     服务层 (Backend API)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │Project   │ │Data      │ │Model     │ │Inference │ Agent   │
│  │Mgmt API  │ │Mgmt API  │ │Build API │ │API       │  API    │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘───┬─────┘
│       │             │            │            │          │
├───────┼─────────────┼────────────┼────────────┼──────────┼─────┤
│                     引擎层 (Core Engine)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │Data      │ │Cleaning  │ │Training  │ │Inference │ Agent   │
│  │Parser    │ │Engine    │ │Engine    │ │Engine    │  Engine │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘───┬─────┘
│       │             │            │            │          │
├───────┼─────────────┼────────────┼────────────┼──────────┼─────┤
│                     数据层 (Persistence)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                      │
│  │PostgreSQL│ │File Store│ │ Model    │                      │
│  │(metadata)│ │(Local FS)│ │ Registry │                      │
│  └──────────┘ └──────────┘ └──────────┘                      │
└──────────────────────────────────────────────────────────────┘
```

**解耦关键设计**：
- 所有模块间通过 REST API 通信，不存在进程内函数调用依赖
- 训练引擎作为独立子进程运行（`subprocess`），与 API 服务进程隔离
- 实时监控通过 WebSocket 推送，不轮询
- 模型文件、数据集文件通过文件系统 UUID 路径共享，不通过 API 传输大文件

---

## 2. 技术栈与架构决策

| 层面 | 选型 | 理由 |
|------|------|------|
| **前端框架** | React 18 + TypeScript + Vite | 生态成熟，Vite HMR 极快，适合极限工期 |
| **UI 组件库** | Ant Design 5.x | 表格/表单/图表组件丰富，开箱即用，省去自定义组件时间 |
| **图表库** | ECharts (via echarts-for-react) | 训练曲线、混淆矩阵、热力图等高密度图表首选 |
| **状态管理** | Zustand | 轻量无样板代码，比 Redux 快 3x 开发效率 |
| **HTTP 请求** | Axios + React Query (TanStack) | 缓存/重试/轮询开箱即用 |
| **Mock** | MSW (Mock Service Worker) | 拦截网络层，FE 零依赖后端开发 |
| **后端框架** | Python 3.10 + FastAPI | 异步高性能，自动生成 OpenAPI 文档，PRD 指定 |
| **ORM** | SQLAlchemy 2.0 + Alembic | 异步支持，迁移管理成熟 |
| **数据库** | PostgreSQL 15（开发期 SQLite 降级） | 生产级，JSONB 适合灵活元数据存储 |
| **文件存储** | 本地文件系统 + 结构化目录 | V1.0 不引入 MinIO/S3，降低运维复杂度 |
| **深度学习** | PyTorch 2.x + torchvision | PRD 指定唯一框架 |
| **推理加速** | ONNX Runtime 1.18+ | PRD 指定 |
| **WebSocket** | FastAPI WebSocket (native) | 训练监控实时推送 |
| **Agent** | OpenAI-compatible API 插件 (LiteLLM) | 多模型供应商兼容 |
| **认证** | OAuth2 + JWT (FastAPI内置) | PRD 要求 |
| **部署** | Docker Compose | 前后端 + 数据库 + GPU 训练容器一键启动 |

---

## 3. 模块与分工矩阵

### 3.1 团队角色配置

| 编号 | 角色 | 姓名 | 定位 |
|------|------|------|------|
| P1 | Tech Lead / 架构师 | TBD | 全局架构、API 契约、Agent 引擎、技术攻坚 |
| P2 | FE Lead | TBD | 项目骨架、路由、状态管理、组件库封装 |
| P3 | FE Dev | TBD | 数据管理 + 数据清洗 & EDA 页面 |
| P4 | FE Dev | TBD | 模型构建 + 训练监控页面 |
| P5 | FE Dev | TBD | 推理 + Agent 构建页面 |
| P6 | BE Dev (Infra) | TBD | API 网关、认证、项目 CRUD、数据库、文件存储 |
| P7 | BE Dev (Data) | TBD | 数据管理 API、数据清洗 API、EDA 服务 |
| P8 | BE Dev (Train) | TBD | 模型构建 API、训练引擎、WebSocket 监控 |
| P9 | QA / DevOps | TBD | 测试用例、CI/CD、Docker、GPU 环境、集成测试 |

### 3.2 详细分工矩阵

| 人员 | 模块 | 核心职责 | 关键交付物 |
|------|------|---------|-----------|
| **P1** | 架构 + Agent 引擎 | ①OpenAPI 3.0 契约制定与维护 ②Agent 引擎（FastAPI 工具封装、对话 Agent、Prompt 管理）③技术选型落地 ④Code Review（所有 BE 代码）⑤每日集成环境维护 | `openapi.yaml`、Agent 服务、集成环境 |
| **P2** | 前端基础设施 | ①Vite + React 脚手架搭建 ②路由设计（React Router）③全局 Layout（侧边栏导航、Header）④Zustand 全局状态（User/Project/Theme）⑤Ant Design 主题定制 ⑥通用组件（FileUpload、DataTable、CodeEditor、Modal）⑦认证页面（Login/Register） | 项目骨架、组件库、路由系统 |
| **P3** | 数据管理 + 清洗页面 | ①数据上传页（拖拽上传、进度条、断点续传）②数据集列表页（CRUD、搜索、标签筛选）③图片数据集画廊页（缩略图、标签绑定、预览）④数据清洗操作页（缺失值/异常值/去重/编码转换 UI）⑤EDA 报告页（统计概览、可视化图表）⑥数据增强配置页（CV 增强参数、预览对比） | 4 个核心页面 + 子组件 |
| **P4** | 模型构建 + 训练页面 | ①模型库浏览页（模型卡片、搜索筛选、一键选用）②参数配置页（学习率、优化器、损失函数、正则化等表单）③训练任务创建页（数据集选择、资源配置、超参确认）④训练任务列表页（状态管理、启停控制）⑤训练监控仪表盘（实时曲线、资源监控、日志流）⑥实验管理页（列表、对比） | 6 个核心页面 + 图表组件 |
| **P5** | 推理 + Agent 页面 | ①模型评估页（评测指标、混淆矩阵图、ROC/PR 曲线）②批量推理页（数据集选择、进度、结果预览）③在线测试页（交互式输入、即时推理结果）④Agent 管理页（列表、创建、工具绑定）⑤Agent 对话页（Chat UI、多轮对话、Prompt 编辑器）⑥对话日志页 | 6 个核心页面 |
| **P6** | 基础设施层 | ①FastAPI 项目骨架搭建 ②用户认证（OAuth2+JWT）③RBAC 权限中间件 ④项目 CRUD API ⑤数据库 Schema（Alembic Migration）⑥文件存储服务（上传/下载/路径管理）⑦API 网关（统一路由、CORS、限流） | 后端骨架、认证系统、数据库 DDL |
| **P7** | 数据层 API + 清洗引擎 | ①数据上传 API（分片上传、格式解析、元数据提取）②数据集 CRUD API ③图片标签绑定 API ④数据清洗引擎（缺失值/异常值/去重/编码转换）⑤EDA 服务（统计计算 + 图表数据生成）⑥数据增强服务（CV 增强：旋转/翻转/色彩/MixUp/CutMix）⑦数据集划分 API | 数据 API 全套 + 清洗/EDA 引擎 |
| **P8** | 模型层 API + 训练引擎 | ①模型库 API（预置模型注册、搜索、详情）②参数配置 API（校验、保存、模板）③训练任务管理 API（创建/启停/状态机）④训练引擎核心（PyTorch 训练循环、混合精度、梯度累积、Checkpoint、早停）⑤WebSocket 训练监控（损失/准确率/学习率实时推送）⑥资源监控（GPU/CPU 利用率采集）⑦预训练权重加载（HuggingFace/ModelScope） | 训练系统全套 |
| **P9** | QA + DevOps | ①测试计划与用例编写 ②FE 组件单元测试（Vitest）③BE API 集成测试（pytest）④端到端流程测试 ⑤Docker Compose 编排（app + db + gpu）⑥CI/CD Pipeline（GitHub Actions）⑦GPU 环境配置文档 ⑧性能基线与压测报告 | 测试套件、部署包、压测报告 |

---

## 4. 并行开发协议

> **这是本计划最核心的章节。所有模块必须在此协议的约束下才能实现真正的同时开工。**

### 4.1 API 契约层（Day1 10:00 冻结）

所有 API 以 OpenAPI 3.0 YAML 文件为唯一真相源（`/docs/api/openapi.yaml`），由 P1 维护，各端据此生成代码。

**强制约束**：

| 约束项 | 规则 |
|--------|------|
| URL 命名 | `/{resource}/{id}/{sub-resource}` 层级不超过 3 层 |
| 请求/响应格式 | 统一 JSON Schema，所有响应包裹 `{code, message, data}` |
| 错误码 | 统一 8 位错误码（模块+类别+序号），见 [附录](#71-统一错误码规范) |
| 分页 | 统一 `{page, page_size, total, items[]}` |
| 文件上传 | 统一 multipart/form-data，分片上传用 `Content-Range` header |
| 版本 | URL Prefix `/api/v1` |
| 认证 | `Authorization: Bearer <JWT>` |

**已确定的核心 API 列表**（Day1 10:00 前完成 Schema 定义）：

<details>
<summary>点击展开完整 API 列表 (50+ Endpoints)</summary>

```
# ============ 认证 (P6) ============
POST   /api/v1/auth/login              # 用户名密码登录
POST   /api/v1/auth/refresh            # 刷新Token
POST   /api/v1/auth/register           # 注册（V1.0 简化）
GET    /api/v1/auth/me                 # 当前用户信息

# ============ 项目管理 (P6) ============
GET    /api/v1/projects                # 项目列表
POST   /api/v1/projects                # 创建项目
GET    /api/v1/projects/{id}           # 项目详情
PUT    /api/v1/projects/{id}           # 更新项目
DELETE /api/v1/projects/{id}           # 删除项目

# ============ 数据管理 (P7) ============
POST   /api/v1/projects/{id}/datasets/upload        # 分片上传
POST   /api/v1/projects/{id}/datasets/upload/init   # 初始化上传（获取upload_id）
POST   /api/v1/projects/{id}/datasets/upload/{uid}/chunk  # 上传分片
POST   /api/v1/projects/{id}/datasets/upload/{uid}/complete # 合并分片
GET    /api/v1/projects/{id}/datasets               # 数据集列表
POST   /api/v1/projects/{id}/datasets               # 创建数据集（元数据注册）
GET    /api/v1/projects/{id}/datasets/{ds_id}       # 数据集详情
GET    /api/v1/projects/{id}/datasets/{ds_id}/preview  # 数据预览（前100行）
GET    /api/v1/projects/{id}/datasets/{ds_id}/images     # 图片画廊（缩略图+标签）
PUT    /api/v1/projects/{id}/datasets/{ds_id}/labels     # 批量更新图片标签
PUT    /api/v1/projects/{id}/datasets/{ds_id}       # 更新数据集
DELETE /api/v1/projects/{id}/datasets/{ds_id}       # 删除数据集

# ============ 数据清洗 (P7) ============
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/missing       # 缺失值处理
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/outlier       # 异常值检测
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/dedup         # 去重
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/encode        # 编码转换
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/type-convert  # 类型转换
POST   /api/v1/projects/{id}/datasets/{ds_id}/eda                 # 一键EDA
GET    /api/v1/projects/{id}/datasets/{ds_id}/eda/report          # 获取EDA报告
POST   /api/v1/projects/{id}/datasets/{ds_id}/augment             # CV数据增强
POST   /api/v1/projects/{id}/datasets/{ds_id}/split               # 数据集划分

# ============ 模型构建 (P8) ============
GET    /api/v1/models/library                # 预置模型库
GET    /api/v1/models/library/{model_id}     # 模型详情
POST   /api/v1/projects/{id}/models          # 创建模型配置
GET    /api/v1/projects/{id}/models          # 项目模型列表
GET    /api/v1/projects/{id}/models/{m_id}   # 模型配置详情
PUT    /api/v1/projects/{id}/models/{m_id}   # 更新模型配置
POST   /api/v1/projects/{id}/models/{m_id}/validate  # 校验参数配置
POST   /api/v1/projects/{id}/models/{m_id}/pretrained # 加载预训练权重

# ============ 训练 (P8) ============
POST   /api/v1/projects/{id}/training-jobs           # 创建训练任务
GET    /api/v1/projects/{id}/training-jobs           # 训练任务列表
GET    /api/v1/projects/{id}/training-jobs/{job_id}  # 任务详情
POST   /api/v1/projects/{id}/training-jobs/{job_id}/start    # 启动
POST   /api/v1/projects/{id}/training-jobs/{job_id}/pause    # 暂停
POST   /api/v1/projects/{id}/training-jobs/{job_id}/resume   # 恢复
POST   /api/v1/projects/{id}/training-jobs/{job_id}/stop     # 终止
WS     /api/v1/ws/training/{job_id}                 # WebSocket 监控流
GET    /api/v1/projects/{id}/training-jobs/{job_id}/logs      # 训练日志
GET    /api/v1/projects/{id}/training-jobs/{job_id}/checkpoints # Checkpoint 列表

# ============ 实验管理 (P8) ============
GET    /api/v1/projects/{id}/experiments           # 实验列表
GET    /api/v1/projects/{id}/experiments/{exp_id}  # 实验详情
PUT    /api/v1/projects/{id}/experiments/{exp_id}  # 更新实验标签/备注
POST   /api/v1/projects/{id}/experiments/compare   # 实验对比

# ============ 推理 (P7/P8) ============
POST   /api/v1/projects/{id}/inference/evaluate    # 模型评估
POST   /api/v1/projects/{id}/inference/batch       # 批量推理
GET    /api/v1/projects/{id}/inference/{task_id}   # 推理结果
POST   /api/v1/projects/{id}/inference/online      # 在线测试（单条）
POST   /api/v1/projects/{id}/inference/export-onnx # 导出ONNX

# ============ Agent (P1) ============
GET    /api/v1/projects/{id}/agents                # Agent 列表
POST   /api/v1/projects/{id}/agents                # 创建 Agent
GET    /api/v1/projects/{id}/agents/{agent_id}     # Agent 详情
PUT    /api/v1/projects/{id}/agents/{agent_id}     # 更新 Agent
DELETE /api/v1/projects/{id}/agents/{agent_id}     # 删除 Agent
POST   /api/v1/projects/{id}/agents/{agent_id}/tools/bind    # 绑定模型工具
POST   /api/v1/projects/{id}/agents/{agent_id}/chat          # 对话（SSE 流式）
GET    /api/v1/projects/{id}/agents/{agent_id}/chat/history  # 对话历史
POST   /api/v1/projects/{id}/agents/{agent_id}/prompts       # 保存 Prompt 模板
GET    /api/v1/projects/{id}/agents/{agent_id}/prompts       # Prompt 模板列表
GET    /api/v1/projects/{id}/agents/{agent_id}/tools         # 已绑定工具列表
```
</details>

### 4.2 数据模型 DDL（Day1 10:00 冻结）

核心表结构由 P6 输出 Alembic migration 脚本，所有 BE 开发基于相同的数据库 Schema。

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   users     │     │   projects   │     │   datasets   │
├─────────────┤     ├──────────────┤     ├──────────────┤
│ id (UUID)   │←───→│ id (UUID)    │←───→│ id (UUID)    │
│ username    │     │ name         │     │ name         │
│ password    │     │ description  │     │ project_id   │
│ role        │     │ owner_id     │     │ format       │
│ created_at  │     │ storage_quota│     │ file_path    │
└─────────────┘     │ created_at   │     │ num_samples  │
                    └──────────────┘     │ columns_meta │(JSONB)
                           │             │ tags         │(JSONB)
                           │             │ status       │
                           │             │ created_at   │
                           │             └──────────────┘
                           │                    │
                           ▼                    ▼
                    ┌──────────────┐     ┌──────────────┐
                    │   models     │     │training_jobs │
                    ├──────────────┤     ├──────────────┤
                    │ id (UUID)    │←───→│ id (UUID)    │
                    │ project_id   │     │ project_id   │
                    │ name         │     │ name         │
                    │ arch_type    │     │ model_id     │
                    │ params_cfg   │(JSONB)│ dataset_id  │
                    │ pretrained   │     │ hyperparams  │(JSONB)
                    │ model_path   │     │ status       │(Enum)
                    │ created_at   │     │ device       │
                    └──────────────┘     │ metrics      │(JSONB)
                           │             │ checkpoint   │
                           │             │ started_at   │
                           │             │ finished_at  │
                           │             └──────────────┘
                           │                    │
                           ▼                    ▼
                    ┌──────────────┐     ┌──────────────┐
                    │  agents      │     │ experiments  │
                    ├──────────────┤     ├──────────────┤
                    │ id (UUID)    │     │ id (UUID)    │
                    │ project_id   │     │ project_id   │
                    │ name         │     │ job_id (FK)  │
                    │ system_prompt│     │ metrics      │(JSONB)
                    │ model_config │(JSONB)│ params_snap  │(JSONB)
                    │ tools        │(JSONB)│ tags         │(JSONB)
                    │ status       │     │ notes        │
                    │ created_at   │     │ created_at   │
                    └──────────────┘     └──────────────┘
```

### 4.3 文件存储规范

```
{STORAGE_ROOT}/
├── projects/
│   └── {project_uuid}/
│       ├── datasets/
│       │   └── {dataset_uuid}/
│       │       ├── raw/              # 原始上传文件
│       │       ├── cleaned/          # 清洗后数据
│       │       └── meta.json         # 元数据
│       ├── models/
│       │   └── {model_uuid}/
│       │       ├── checkpoint/       # .pth 文件
│       │       └── exported/         # .onnx 文件
│       └── experiments/
│           └── {experiment_uuid}/
│               └── logs/             # 训练日志
└── uploads/                          # 临时上传分片
```

### 4.4 WebSocket 协议（训练监控）

```
方向: Server → Client
消息格式: JSON

# 训练指标推送
{
  "type": "metrics",
  "data": {
    "epoch": 5,
    "step": 250,
    "train_loss": 0.342,
    "val_loss": 0.521,
    "accuracy": 0.87,
    "learning_rate": 0.001,
    "gpu_util": 85,
    "gpu_memory": 75,
    "cpu_util": 45,
    "memory_util": 62,
    "throughput": "125 samples/s",
    "eta": "5m 30s"
  }
}

# 消息类型枚举
types: ["metrics", "log", "alert", "status_change", "progress"]
```

### 4.5 Mock 数据策略

| 端 | Mock 方案 | 细节 |
|----|-----------|------|
| **FE** | MSW (Mock Service Worker) + `@/mocks/handlers/` | 每个模块维护自己的 handler，返回符合契约的假数据 |
| **BE 单元测试** | pytest + factory_boy + SQLite | 内存数据库跑测试，每个测试隔离 |
| **FE ↔ BE 联调** | 共享 Mock Server 脚本 `scripts/mock_server.py` | 可独立启动的 Flask/FastAPI 服务，返回静态数据 |
| **训练引擎测试** | 合成数据集生成器 `scripts/gen_synthetic_data.py` | 生成 CSV + 随机图像，5秒可完成一个 epoch 的小规模训练 |

### 4.6 解除物理耦合的依赖注入

```python
# 示例：P7 的数据清洗 API 在开发期不依赖真实数据集存储
class CleaningService:
    def __init__(self, storage: StorageProtocol):  # 接口，非具体实现
        self.storage = storage

# P7 和 P6 并行开发时，P7 用 MockStorage，P6 用 RealStorage
# Day3 联调时替换为：CleaningService(storage=RealFileStorage())
```

**关键接口（Python Protocol 类）全部定义在 `src/shared/protocols.py` 中，Day1 10:00 冻结。**

---

## 5. 4天冲刺时间表

### 5.1 总览

```
Day1 ───────  Day2 ───────  Day3 ───────  Day4 ───────
[基石]        [核心功能]     [联调+Agent]   [收尾+交付]
P0 全部开工   P0 批量完成    P0 端到端打通  P0 Bug修复
P1 部分开工   P1 并行推进    P1 功能补齐    P1 测试验收
              首次集成测试  全面集成测试   交付评审
```

### 5.2 Day 1：地基日 "契约冻结，全线开工"

| 时间 | 里程碑 | 产出 |
|------|--------|------|
| **09:00** | 🔵 CP1：站会 | P1 发布最终技术选型与架构图；全队对齐分工 |
| **10:00** | 🔴 M1-A：契约冻结 | `openapi.yaml` 完成（P1）；DDL Migration 完成（P6）；`protocols.py` 完成（P1）；文件存储规范确认 |
| **12:00** | 🔵 CP2：午间集成 | P2 完成 Vite + React 脚手架 + 路由（含 Mock 接入）；P6 完成 FastAPI 骨架 + 数据库连接 + `/health` 端点；P7/P8 完成各自 FastAPI Router 骨架 + 第一版 Mock handler |
| **14:00** | 继续开发 | **FE**：P3 开始上传页面，P4 开始模型库页面，P5 开始推理页面（均用 Mock 数据）；**BE**：P6 完成认证 API + 项目 CRUD API；P7 完成数据上传 API（不含清洗）；P8 完成模型库 API（返回预置模型列表静态 JSON） |
| **18:00** | 🔵 CP3：晚间站会 | ①所有 API `/docs` Swagger 页面可访问（含 Mock 实现）②FE 至少 1 个页面渲染出 Mock 数据③P1 检查所有 API 是否符合契约④阻塞问题上报 |
| **18:00-22:00** | 夜间冲刺（可选） | P8 开始训练引擎核心（合成数据 + 最小训练循环验证 PyTorch 通路）；P7 开始数据清洗引擎骨架；P9 Docker Compose 编排文件初版 |

**Day 1 验收标准**：
- [ ] `openapi.yaml` 已推送到仓库（Git tag: `contract-v1`）
- [ ] 所有 API 端点已注册路由（返回 Mock 数据/501）
- [ ] FE 能启动并看到导航 + 至少 1 个列表页
- [ ] Postman/curl 能访问任意后端 API 并获得响应
- [ ] 数据库表已创建（Alembic head 可执行）
- [ ] Docker Compose 能启动 `app + db`

### 5.3 Day 2：功能日 "P0 全线推进"

| 时间 | 里程碑 | 产出 |
|------|--------|------|
| **09:00** | 🔵 CP4：站会 | 检查 Day1 未完成项；P1 发布 Agent 引擎技术方案；确认 Day2 目标 |
| **12:00** | 🔵 CP5：午间集成 | **FE P3**：数据上传页功能完成 + 数据预览页 + 图片画廊页（Mock）；**FE P4**：模型库浏览页 + 参数配置表单；**FE P5**：推理评估页 + 在线测试页骨架；**BE P7**：数据清洗引擎完成（缺失值/异常值/去重）+ EDA 统计计算完成；**BE P8**：训练循环核心完成（合成数据上可跑通完整训练） |
| **14:00** | 挑战 P0 完成 | P7：数据增强服务完成；P8：WebSocket 监控推送完成、Checkpoint 机制完成、早停机制完成；P6：文件存储服务完成 |
| **18:00** | 🔴 M2：P0 功能封版 | **所有 P0 功能后端 API 返回真实数据**（非 Mock）；FE P3/P4/P5 页面结构完成（仍可用 Mock）；P1 Agent 引擎 FastAPI 工具封装核心逻辑完成 |
| **18:00-22:00** | 🔵 CP6：首次集成测试 | P9 执行首次自动化集成测试；FE ↔ BE 逐接口对接；发现并记录 Bug 列表 |

**Day 2 验收标准**：
- [ ] 后台上传 CSV/JSON/图像 → API 返回解析后的预览数据
- [ ] 数据清洗各操作可执行并返回结果
- [ ] 训练引擎在合成数据集上可完成一次完整训练（含 Checkpoint 保存）
- [ ] WebSocket 可推送训练指标
- [ ] 前端所有 P0 页面路由可达，结构完整
- [ ] Agent 引擎可生成 FastAPI 路由代码并启动

### 5.4 Day 3：集成日 "端到端打通"

| 时间 | 里程碑 | 产出 |
|------|--------|------|
| **09:00** | 🔵 CP7：站会 | 回顾 Day2 Bug 列表；P1 分配阻塞问题攻坚任务；确认 Day3 目标 |
| **09:00-12:00** | FE Mock → 真实 API 切换 | P3/P4/P5 逐模块切换至真实后端；P7/P8 修复联调发现的接口不匹配问题 |
| **12:00** | 🔵 CP8：模块联调完成 | **P0 全链路可走通**：上传数据 → 清洗 → 选模型 → 配参数 → 训练（最小数据集一次 epoch）→ 看到损失曲线 → 推理 → 得到结果 |
| **14:00** | P1 功能补齐 | P3：EDA 图表真实数据接入 + 数据增强页面；P4：实验管理功能；P5：Agent 对话 UI 接入真实 Agent API；P1 + P5：Agent 对话 + 模型工具调用端到端打通 |
| **18:00** | 🔴 M3：端到端演示 | **全流程可演示**：任何模块的组合流程都可走通；P1 + P9 组织内部演示会，收集反馈 |
| **18:00-22:00** | 🔵 CP9：Bug Bash | 全员修 Bug；P9 回归测试；性能优化（API 响应时间、前端加载速度） |

**Day 3 验收标准**：
- [ ] 场景一（商品图像分类）全流程可走通
- [ ] 场景二（业务数据回归预测）全流程可走通
- [ ] WebSocket 训练监控实时数据正常
- [ ] Agent 对话可绑定模型工具并完成一次对话推理
- [ ] 无 P0 阻塞 Bug
- [ ] API 文档（Swagger）与实际实现一致

### 5.5 Day 4：交付日 "抛光与上线"

| 时间 | 里程碑 | 产出 |
|------|--------|------|
| **09:00** | 🔵 CP10：站会 | 盘点剩余 P1 功能 + Bug 数量；决定哪些砍掉、哪些修复 |
| **09:00-12:00** | P0 Bug 清零 + P1 收尾 | P9：全量回归测试 + 性能压测；P2：UI 打磨（Loading 态、空状态、错误提示、响应式适配）；全员：修复 P0 Bug |
| **12:00** | 🔵 CP11：代码冻结 | 不再合入新功能；仅允许 Bug 修复和文档更新；P9 执行最终集成测试 |
| **14:00** | P1 文档 + 帮助 | P2 输出前端操作指南；P1 输出 API 文档 + 快速上手文档；P9 输出部署文档 |
| **16:00** | 🔴 M4：交付评审 | 正式演示（4 个典型场景逐一走通）；P1 做交付汇报（完成度、遗留问题、后续建议） |
| **18:00** | 🔵 CP12：最终站会 | 交付物清单确认；Git Tag `v1.0.0`；CI/CD 构建通过；Docker 镜像推送 |

**Day 4 验收标准**：
- [ ] 4 个典型使用场景均可流畅演示
- [ ] P0 Bug 为 0，P1 Bug < 5
- [ ] API 文档 + 用户手册 + 部署文档 三件套齐全
- [ ] Docker Compose 一键启动可运行
- [ ] 性能指标达标（API P95 < 500ms，训练启动 < 30s）

---

## 6. 风险提示与阻碍预案

### 6.1 风险矩阵

| # | 风险项 | 概率 | 影响 | 缓解措施 | 触发应急预案的条件 |
|----|--------|------|------|---------|-------------------|
| R1 | **API 契约设计与实际实现偏差大** | 高 | 高 | Day1 10:00 强制冻结；P1 每小时检查各端实现与契约的一致性；契约修改走 P1 审批 | Day2 中午仍有 >5 个接口不匹配 → P1 介入逐一定版 |
| R2 | **训练引擎 GPU 环境搭建拖延** | 高 | 高 | Day1 即由 P9 验证 CUDA/PyTorch 可用；训练引擎先跑 CPU 模式验证逻辑，GPU 作为优化项 | Day2 18:00 前 GPU 不可用 → 降级为 CPU-only 交付，GPU 模式作为 V1.1 |
| R3 | **Agent 对话 LLM API 不可用或无配额** | 中 | 高 | Agent 引擎支持模拟 LLM 模式（`MockLLM`），返回预设回复；先验证工具调用链路，LLM 可后接 | Day3 12:00 前无法获得 API Key → 用 MockLLM 演示，对话为固定模板回复 |
| R4 | **前端页面过多，4 天无法全部完成 UI 细节** | 高 | 中 | **核心路径优先**：上传→清洗→选模型→训练→推理 的 UI 必须完整；Agent 对话页可用简化版（单轮对话）；EDA 图表用 Ant Design Charts 模板快速搭建 | Day3 仍有 >3 个页面骨架不可用 → P1 决定砍掉非关键页面，用 placeholder 占位 |
| R5 | **文件上传大文件（5GB）性能不达标** | 中 | 中 | Day1 即实现分片上传架构；V1.0 内测阶段用 <100MB 文件验证；5GB 测试仅做架构验证 | 分片上传逻辑 Day2 18:00 前不可用 → 降级为单次上传（限 500MB） |
| R6 | **训练任务中的复杂状态机出现 Bug** | 中 | 高 | 状态机用枚举 + 数据库事务保证一致性；P8 必须先写状态机单元测试再写实现 | 暂停/恢复功能 Day3 中午不稳定 → 砍掉暂停/恢复，仅保留启动/终止 |
| R7 | **某人因故无法完成任务（病假/紧急）** | 低 | 高 | P1 作为后备可接手任何 BE 模块；P2 作为后备可接手 FE 任务；每个模块必须每天都提交代码（不能攒到最后一天） | 任一成员离线 >4 小时 → P1 重分配任务，降级该模块的非 P0 功能 |
| R8 | **预训练权重下载慢或不可访问** | 中 | 低 | 提前在 Day1 下载好 ResNet-18（最小可用模型）到项目内作为默认权重；HuggingFace 下载作为可选增强 | 用随机初始化的 ResNet-18 跑通训练链路（准确率不计） |

### 6.2 Team Lead 每日必须执行的检查

| 时间 | 检查项 |
|------|--------|
| **日间每小时** | ①`git push` 是否成功（任何人不得有未推送的超过 2h 的本地代码）②`/docs` Swagger 是否可访问且与实际实现一致 ③FE `npm run dev` 是否正常启动 |
| **每日 12:00** | ①集成环境是否可用 ②P0 功能列表完成度 ③阻塞项列表是否清零 |
| **每日 18:00** | ①当日计划完成度 ②是否有人需要支援 ③是否有人偏离计划方向 |

### 6.3 优先级降级预案

**如果时间不够，按以下顺序砍功能**：

| 砍的顺序 | 功能 | 理由 |
|-----------|------|------|
| 1 | EDA 质量评分（P1） | 可以手动看统计报告替代 |
| 2 | 数据增强预览对比（P1） | 增强后可手动验证 |
| 3 | 实验对比（P1） | 列表查看可替代 |
| 4 | 对话日志（P1） | 不影响核心链路 |
| 5 | ROC/PR 曲线（P1） | 准确率等基本指标足够 |
| 6 | 混淆矩阵（P1） | 同上 |
| 7 | 参数模板（P1） | 手动配置可替代 |
| 8 | 目录上传（P1） | 批量上传可替代 |
| 9 | ONNX Runtime 加速（P1） | PyTorch 原生推理可替代 |

**P0 功能绝对不可砍**清单：
- 数据上传（拖拽+批量+预览+图片标签绑定+画廊）
- 数据清洗（缺失值/异常值/去重/编码转换）
- 自动化 EDA（统计概览+分布可视化）
- CV 数据增强（旋转/翻转/色彩/MixUp+强度选择）
- 预置模型库（ResNet-18/34/50 + EfficientNet + MLP）
- 参数化配置（学习率/优化器/损失函数/Batch Size/正则化）
- 单任务训练（启动/终止 + 混合精度 + 梯度累积）
- 训练监控（实时曲线 + 资源监控 + 日志 + 异常告警）
- Checkpoint + 早停
- 批量推理 + 在线测试
- 模型评估（一键评估）
- Agent 对话模板 + FastAPI 工具封装 + 工具绑定
- 多轮对话 + Prompt 管理

---

## 7. 附录：API契约速查

### 7.1 统一错误码规范

```
格式: XX-YY-ZZZ
  XX: 模块代码
  YY: 错误类别
  ZZZ: 序号

模块代码:
  10 - 认证 (Auth)
  20 - 项目 (Project)
  30 - 数据集 (Dataset)
  40 - 模型 (Model)
  50 - 训练 (Training)
  60 - 推理 (Inference)
  70 - Agent

错误类别:
  01 - 参数错误
  02 - 资源不存在
  03 - 权限不足
  04 - 业务逻辑错误
  05 - 系统错误

示例:
  30-04-001: 数据集已被训练任务引用, 无法删除
  50-02-001: 训练任务不存在
```

### 7.2 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "request_id": "uuid-v4"
}
```

### 7.3 Git 分支策略

```
main                  # 生产就绪（Day4 最终交付）
  └── develop         # 集成开发（每日 12:00 / 18:00 强制合并）
        ├── feat/data-management    # P3 + P7
        ├── feat/data-cleaning      # P3 + P7
        ├── feat/model-building     # P4 + P8
        ├── feat/training           # P4 + P8
        ├── feat/inference          # P5 + P7/P8
        ├── feat/agent              # P5 + P1
        ├── feat/infra              # P2 + P6
        └── feat/devops             # P9
```

**合并规则**：
- 每日 12:00 和 18:00，P1 强制将所有 `feat/*` 合并到 `develop`
- 合并冲突由 P1 协调解决
- 禁止直接 push 到 `main` 和 `develop`

### 7.4 沟通与协作公约

| 规则 | 内容 |
|------|------|
| 每日站会 | 09:00，不超过 10 分钟，只说 3 件事：昨天做了什么、今天要做什么、有什么阻塞 |
| 即时通讯 | 微信群/飞书群 + 共享文档（Notion/飞书文档），P1 在频道中每小时同步一次进度 |
| 代码审查 | 所有 PR 必须至少 1 人 Approve；P1 审查所有 BE PR；P2 审查所有 FE PR |
| 提交粒度 | 每完成一个子功能立即 commit + push，不得攒超过 2 小时 |
| Commit Message | `feat(module): description` / `fix(module): description` / `docs: description` |

---

## 8. 关键角色备份矩阵

```
如果 P2 (FE Lead) 离线 → P3 接手路由/状态管理，P5 接手共享组件
如果 P6 (Infra BE) 离线 → P1 接手认证/项目API，P7 接手文件存储
如果 P7 (Data BE) 离线 → P8 接手数据API，P1 接手清洗引擎
如果 P8 (Train BE) 离线 → P1 接手训练引擎
如果 P3/P4/P5 (FE) 离线 → P2 重新分配页面优先级，砍非P0页面
如果 P9 (QA/DevOps) 离线 → P1 接手集成测试，P6 接手Docker
如果 P1 离线 → P2 代理 Team Lead 角色
```

---

*本计划为 DeepFlow V1.0 实施的纲领性文件，由架构师 & Team Lead 签发。所有团队成员需在开工前阅读并确认。*
