# DeepFlow PRD V1.0 - 4天并行开发作战方案

## 1. 架构师全局视角

### 1.1 交付目标定义

本次目标不是在 4 天内完整实现 PRD 的全部能力，而是以 `P0 主链路可交付` 为第一优先级，完成 DeepFlow 从数据上传到 Agent 调用的端到端闭环，确保项目具备可演示、可联调、可部署的 MVP 版本。

建议本轮团队配置如下：

- 3 个前端工程师
- 4 个后端/算法工程师
- 1 个测试工程师
- 1 个 DevOps 工程师

### 1.2 并行开发核心策略

为了实现 9 人同时开工，本项目必须遵循以下策略：

- **契约先行**：Day 1 上午先冻结 OpenAPI、核心实体结构、状态机和错误码，不等实现先定接口。
- **前后端物理解耦**：前端基于 OpenAPI + Mock Server 独立开发，后端按契约补真实实现。
- **异步流程标准化**：训练、推理、EDA、增强统一抽象为异步任务，状态统一为 `pending/running/success/failed/cancelled/paused`。
- **主链路优先**：优先打通 `数据上传 -> 数据清洗/EDA -> 模型选择 -> 训练 -> 推理 -> Agent`，P1/P2 一律不得阻塞联调。
- **轻量集成**：逻辑上分层，部署上可合并为少量服务，避免因微服务治理拖慢交付。
- **每日两次收口**：上午定阻塞、下午定联调、晚上定合并，严格控制范围蔓延。

### 1.3 代码集成策略

4 天极限工期建议采用 **GitHub Flow 的轻量变体**：

- 主分支：`main`
- 集成分支：`develop`
- 模块开发从 `develop` 拉出短命分支
- 每个分支生命周期控制在半天到 1 天
- 所有合并先入 `develop`，当天通过冒烟测试后按节奏合并到 `main`
- `main` 仅保留可发布状态，禁止直接提交

### 1.4 Git 分支命名规范

统一命名格式：

```text
feature/<module>-<owner>-<short-task>
fix/<module>-<owner>-<short-task>
hotfix/<module>-<short-task>
release/day<1|2|3|4>-rc
```

示例：

```text
feature/data-fe-li-upload-page
feature/train-be-wang-job-runner
feature/agent-be-chen-chat-endpoint
fix/frontend-fe-zhao-loading-state
release/day3-rc
```

### 1.5 合并规则

- 小步提交，每个 PR 聚焦一个最小可验证能力
- PR 大小建议控制在 `300` 行核心变更以内
- 至少 1 人 Review，紧急情况下由 Team Lead 快速 Review
- 合并前必须满足：
  - 本地能跑
  - 接口契约未破坏
  - 冒烟测试通过
  - 页面无阻塞级报错
- 任何跨模块字段变更必须先同步契约文档，再允许合并

---

## 2. 模块与分工矩阵

### 2.1 逐人分工说明

#### A - 架构师 / Team Lead

- 负责冻结 MVP 范围、核心实体、OpenAPI 契约、状态机和错误码规范
- 负责每日站会、联调会、Merge 节点把控和风险裁剪
- 负责跨模块冲突仲裁，尤其是接口字段变更、目录结构调整、发布节奏控制
- Day 1 核心产出：架构图、接口清单、共享 schema、Git 规则
- Day 2-4 核心产出：联调问题清单、每日发布决策、最终验收与复盘

#### B - 前端1

- 负责项目工作台和数据管理相关页面
- 负责项目列表/详情、数据集列表、上传页、数据预览、图片缩略图和标签展示
- 主要对接 E 的数据资产服务接口
- Day 1 核心产出：数据管理页面骨架和 Mock 联调
- Day 2 核心产出：接入真实上传、预览、数据集查询接口
- Day 3-4 核心产出：优化空状态、错误态、上传反馈和演示体验

#### C - 前端2

- 负责数据处理和模型配置相关页面
- 负责清洗配置表单、EDA 报告页、增强模板页、模型选择页、超参配置页
- 主要对接 F 的数据处理服务和 G 的模型/训练配置接口
- Day 1 核心产出：表单页和报告页壳层、Mock 数据渲染
- Day 2 核心产出：接入清洗、EDA、模型列表、训练配置提交接口
- Day 3-4 核心产出：补交互校验、参数默认值和演示路径优化

#### D - 前端3

- 负责训练监控、推理测试和 Agent 对话页面
- 负责训练任务列表、日志查看、指标曲线、在线测试页、Agent 聊天页
- 主要对接 G 的训练接口和 H 的推理/Agent 接口
- Day 1 核心产出：训练、推理、Agent 三个页面骨架
- Day 2 核心产出：接入任务状态轮询、日志、推理结果和聊天接口
- Day 3-4 核心产出：完善联调体验、异常提示和正式演示脚本页面

#### E - 后端1

- 负责数据资产服务
- 负责文件上传、元数据抽取、数据预览、图片标签绑定、数据集管理、存储抽象
- 对下游输出标准化的 `Dataset` 和预览数据结构
- Day 1 核心产出：服务 skeleton、上传接口 stub、样例数据集
- Day 2 核心产出：真实上传与预览能力、数据集管理接口
- Day 3-4 核心产出：稳定性修复、文件路径与元数据一致性校验

#### F - 后端2

- 负责数据处理服务
- 负责缺失值处理、异常检测、去重、EDA 统计、数据集划分、增强模板执行
- 对下游输出清洗后数据集、统计报告和 split 结果
- Day 1 核心产出：接口骨架、EDA/清洗 Mock 结果
- Day 2 核心产出：最小真实清洗和 EDA 结果
- Day 3-4 核心产出：增强模板、数据质量问题修复和联调补丁

#### G - 后端3

- 负责模型与训练服务，是本轮最关键的核心 owner
- 负责模型库、参数模板、训练任务创建、状态流转、日志、指标、Checkpoint、早停
- 对上游消费 `ModelSpec` 和数据集信息，对下游输出模型 artifact 与训练状态
- Day 1 核心产出：训练任务状态机、训练接口 stub、假日志和假指标
- Day 2 核心产出：真实训练任务创建与状态查询
- Day 3-4 核心产出：端到端训练跑通、日志曲线稳定、阻塞 bug 修复

#### H - 后端4

- 负责推理与 Agent 服务
- 负责模型评估、在线测试、批量推理、FastAPI 工具封装、Agent 对话接口
- 对上游消费训练产物，对前端提供推理和聊天调用能力
- Day 1 核心产出：推理/Agent 接口骨架和 Mock Tool
- Day 2 核心产出：在线推理闭环、Agent 对话最小能力
- Day 3-4 核心产出：真实工具调用替换、演示脚本和结果稳定性优化

#### I - 测试 / DevOps

- 负责环境、CI、Mock、测试、发布和验收保障
- 负责初始化脚本、环境变量模板、容器/启动脚本、冒烟测试、接口回归、发布流程
- 负责维护 `develop` 和 `release/*` 分支的集成可用性
- Day 1 核心产出：环境模板、Mock 环境、基础 CI 和测试清单
- Day 2 核心产出：数据链路和训练链路冒烟测试
- Day 3-4 核心产出：回归测试、预发布验证、最终发布检查单

### 2.2 分工矩阵

| 人员 | 角色 | 负责模块 | Git 分支名 | 核心职责 |
|---|---|---|---|---|
| A | 架构师 / Team Lead | 全局架构、接口契约、联调指挥 | `feature/arch-lead-global-contracts` | 冻结核心实体、OpenAPI、状态机、排期与风险决策，主持每日 Merge 和联调 |
| B | 前端1 | 项目工作台、数据管理 UI | `feature/data-fe-li-workbench-upload` | 项目页、数据集列表、上传页、数据预览、图片缩略图与标签展示 |
| C | 前端2 | 数据处理与模型配置 UI | `feature/process-fe-zhou-clean-trainform` | 清洗表单、EDA 页面、增强配置、模型选择、超参配置页 |
| D | 前端3 | 训练监控、推理、Agent UI | `feature/train-fe-wu-monitor-agent` | 训练任务页、日志指标曲线、在线测试页、Agent 对话页 |
| E | 后端1 | 数据资产服务 | `feature/data-be-lin-dataset-service` | 数据上传、元数据抽取、预览、标签绑定、数据集管理、存储抽象 |
| F | 后端2 | 数据处理服务 | `feature/process-be-he-clean-eda` | 缺失值处理、异常检测、去重、EDA 统计、数据集划分、增强模板执行 |
| G | 后端3 | 模型与训练服务 | `feature/train-be-wang-training-core` | 模型库、参数模板、训练任务创建、状态管理、日志、Checkpoint、早停 |
| H | 后端4 | 推理与 Agent 服务 | `feature/agent-be-chen-infer-chat` | 模型评估、批量推理、在线测试、FastAPI 工具封装、Agent 对话接口 |
| I | 测试 / DevOps | 环境、CI、测试、发布 | `feature/qaops-sun-ci-smoke` | Docker/脚本、Mock 环境、冒烟测试、接口回归、部署脚本、发布验证 |

### 2.3 模块边界说明

| 模块 | 边界定义 | 是否 P0 | 并行说明 |
|---|---|---|---|
| 数据管理 | 上传、预览、标签绑定、数据集元信息 | 是 | 可独立于训练模块先行完成 |
| 数据处理 | 清洗、EDA、划分、增强模板 | 是 | 基于固定数据结构独立开发 |
| 模型配置 | 预置模型、参数模板、配置表单 | 是 | 只依赖 `ModelSpec` 契约 |
| 训练执行 | 任务提交、状态机、日志、指标、Checkpoint | 是 | 与 UI、推理通过任务输出契约连接 |
| 推理评估 | 在线测试、批量推理、基础评估 | 是 | 只依赖模型产物元数据 |
| Agent | 模型工具封装、对话调用 | 是 | 先基于 Mock Tool 开发，不等待真实模型 |
| 测试与交付 | 环境、CI、回归、发布 | 是 | 从 Day 1 开始介入，不做最后兜底 |

---

## 3. 并行开发协议

### 3.1 核心实体契约

#### `Dataset`

```json
{
  "id": "ds_001",
  "projectId": "proj_001",
  "name": "retina-images",
  "type": "image",
  "format": "jpeg",
  "sampleCount": 1200,
  "status": "ready",
  "tags": ["train"],
  "storagePath": "/data/proj_001/datasets/ds_001",
  "createdAt": "2026-05-18T10:00:00Z"
}
```

#### `ModelSpec`

```json
{
  "id": "model_resnet18",
  "taskType": "classification",
  "framework": "pytorch",
  "architecture": "resnet18",
  "defaultParams": {
    "lr": 0.001,
    "batchSize": 32,
    "epochs": 10,
    "optimizer": "adam",
    "loss": "cross_entropy"
  }
}
```

#### `TrainingJob`

```json
{
  "id": "train_001",
  "datasetId": "ds_001",
  "modelSpecId": "model_resnet18",
  "status": "running",
  "params": {
    "device": "gpu",
    "mixedPrecision": true,
    "gradAccumSteps": 1
  },
  "metrics": {
    "trainLoss": 0.42,
    "valLoss": 0.51,
    "accuracy": 0.89
  },
  "artifact": {
    "bestModelPath": "/artifacts/train_001/best.pth",
    "labelMapPath": "/artifacts/train_001/label_map.json"
  }
}
```

#### `Agent`

```json
{
  "id": "agent_001",
  "name": "retina-assistant",
  "toolEndpoint": "/tools/model/retina-grade/predict",
  "promptTemplate": "你是一个辅助诊断助手",
  "status": "active"
}
```

### 3.2 API 先行约定

以下接口必须在 **Day 1 中午前冻结**：

#### 数据管理 API

- `POST /api/projects`
- `POST /api/datasets/upload`
- `GET /api/datasets`
- `GET /api/datasets/{id}`
- `GET /api/datasets/{id}/preview`

#### 数据处理 API

- `POST /api/datasets/{id}/clean`
- `POST /api/datasets/{id}/eda`
- `POST /api/datasets/{id}/split`
- `POST /api/datasets/{id}/augment`

#### 模型与训练 API

- `GET /api/model-specs`
- `POST /api/training-jobs`
- `GET /api/training-jobs/{id}`
- `POST /api/training-jobs/{id}/action`
- `GET /api/training-jobs/{id}/logs`
- `GET /api/training-jobs/{id}/metrics`

#### 推理与 Agent API

- `POST /api/inference-jobs`
- `GET /api/inference-jobs/{id}`
- `POST /api/agents`
- `POST /api/agents/{id}/chat`

### 3.3 统一响应规范

#### 成功响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

#### 错误响应

```json
{
  "code": 500100,
  "message": "training job failed",
  "details": "CUDA out of memory",
  "traceId": "trace_xxx"
}
```

#### 分页响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "pageSize": 20
  }
}
```

### 3.4 模块链接依赖与解耦方式

| 上游模块 | 下游模块 | 链接依赖 | 解耦策略 |
|---|---|---|---|
| 数据管理 | 数据处理 | 数据集 ID、样本路径、字段信息 | 提前提供示例数据集和元数据 JSON，数据处理先基于样本开发 |
| 数据处理 | 训练 | `processedDatasetId`、split 结构、特征信息 | 训练服务先读取固定目录格式，不等待真实清洗结果 |
| 模型配置 | 训练 | `ModelSpec`、超参数 Schema | 先冻结字段，页面与训练服务独立开发 |
| 训练 | 推理 | 模型路径、标签映射、任务类型 | 训练输出统一 artifact 结构，推理只消费元数据 |
| 推理 | Agent | Tool endpoint、请求/响应结构 | Agent 先接 Mock Tool，Day 3 替换真实接口 |
| 后端 | 前端 | OpenAPI、错误码、状态枚举 | 前端先接 Mock Server，后续无感切换真实接口 |
| DevOps | 全员 | 环境变量、目录结构、启动命令 | Day 1 提供 `.env.example`、初始化脚本、容器或本地模板 |

### 3.5 Mock 数据策略

| 场景 | Mock 策略 | 目的 |
|---|---|---|
| 数据上传列表 | 预置 2 套样例数据集 | 前端不等待真实上传完成 |
| EDA 报告 | 固定 JSON + 图表占位图 | 先完成报告页和交互逻辑 |
| 训练任务 | 定时模拟状态流转 | 提前完成监控页、日志页联调 |
| 推理结果 | 固定预测值与置信度 | 在线测试和批量结果页先交付 |
| Agent 对话 | 固定 Prompt + Tool 回包 | 先完成聊天体验和工具展示 |

### 3.6 工程目录建议

```text
deepflow/
  frontend/
  services/
    api-server/
    data-service/
    training-worker/
    inference-agent-service/
  shared/
    openapi/
    schemas/
    mock-data/
  scripts/
  docs/
```

---

## 4. 4天冲刺时间表

### 4.1 优先级定义

| 优先级 | 范围 |
|---|---|
| P0 | 数据上传、预览、基础清洗、EDA、模型选择与超参配置、单任务训练、训练监控、基础评估、在线测试、Agent 工具绑定 |
| P1 | 增强模板、实验列表、混淆矩阵、训练报告、ONNX Runtime 加速、对话日志 |
| P2 | 高级编排、复杂权限体系、性能深度优化、扩展生态能力 |

### 4.2 Day 1：定边界、建骨架、全员开工

#### 上午 Milestone

- 冻结 MVP 范围和核心实体
- 完成 OpenAPI 初版和 Mock 数据
- 初始化仓库结构、分支策略、环境模板

#### 上午 Checkpoints

| 时间 | Checkpoint | 输出物 |
|---|---|---|
| 09:00 | 冲刺启动会 | 确认 P0/P1 边界、Owner、演示目标 |
| 10:30 | 架构与契约评审 | 核心实体、状态机、错误码、OpenAPI 草案 |
| 11:30 | 第一次代码 Merge 节点 | `develop` 合入项目骨架、Mock、共享 schema |

#### 下午 Milestone

- 前端三块主页面全部起壳
- 后端四个服务 skeleton 可启动
- 测试与 DevOps 完成基础环境

#### 下午 Checkpoints

| 时间 | Checkpoint | 输出物 |
|---|---|---|
| 14:00 | 模块开工同步 | 各分支开始开发，接口 owner 明确 |
| 16:30 | 第一次联调节点 | 前端接 Mock，后端基础路由打通 |
| 18:30 | 第二次代码 Merge 节点 | 各模块 skeleton 合入 `develop` |
| 20:30 | 晚间收口会 | 确认 Day 2 真链路实现顺序 |

### 4.3 Day 2：P0 主功能落地，假链路转真链路

#### 上午 Milestone

- 上传、预览、元数据抽取完成
- 清洗和 EDA 返回真实结果
- 前端开始切换真实接口

#### 上午 Checkpoints

| 时间 | Checkpoint | 输出物 |
|---|---|---|
| 09:00 | 站会 | 确认 blocker 和当天目标 |
| 10:30 | 数据链路联调 | 上传、预览、清洗、EDA 主路径可跑 |
| 12:00 | 中午代码 Merge 节点 | 数据相关模块合入 `develop` |

#### 下午 Milestone

- 训练任务创建、状态查询、日志和指标页打通
- 推理接口、在线测试页可跑
- Agent 页面接上 Mock Tool 或半真实 Tool

#### 下午 Checkpoints

| 时间 | Checkpoint | 输出物 |
|---|---|---|
| 15:00 | 训练链路联调 | 创建任务、查看状态、查看日志和曲线 |
| 17:30 | 推理/Agent 联调 | 在线测试、聊天页请求闭环跑通 |
| 19:00 | 晚间代码 Merge 节点 | 训练、推理、Agent 模块合入 `develop` |
| 20:30 | 晚间收口会 | 判定 P0 完成率，筛选 P1 是否进入 Day 3 |

### 4.4 Day 3：端到端联调、缺陷清理、少量 P1 插入

#### 上午 Milestone

- 首次真实端到端链路联调成功
- 可演示至少 1 个图像分类场景和 1 个表格回归/分类场景

#### 上午 Checkpoints

| 时间 | Checkpoint | 输出物 |
|---|---|---|
| 09:00 | 站会 | 仅讨论阻塞联调问题 |
| 10:30 | 端到端演练 1 | 从上传数据到 Agent 返回结果完整跑通 |
| 12:00 | 中午代码 Merge 节点 | 联调修复项合入 `develop` |

#### 下午 Milestone

- 修复阻塞缺陷
- 选择性补最有展示价值的 P1
- 准备正式演示脚本

#### 建议插入的 P1

- 实验列表
- 增强模板
- 混淆矩阵
- 训练报告
- 基础对话日志

#### 下午 Checkpoints

| 时间 | Checkpoint | 输出物 |
|---|---|---|
| 15:00 | 第二次联调节点 | 场景回归通过，问题列表收敛 |
| 18:00 | 预发布代码 Merge 节点 | 生成 `release/day3-rc` |
| 20:00 | 发布预演 | 按正式环境脚本完成部署演练 |

### 4.5 Day 4：稳定性冲刺、验收、交付

#### 上午 Milestone

- 全部 P0 完成验收
- 完成高优先级 Bug 修复
- 文档、部署脚本、演示材料齐备

#### 上午 Checkpoints

| 时间 | Checkpoint | 输出物 |
|---|---|---|
| 09:00 | 最终冲刺站会 | 只接受 P0 缺陷和发布阻塞 |
| 10:30 | 验收联调节点 | 全链路验收单逐项勾验 |
| 12:00 | 候选版本 Merge 节点 | `release/day4-rc` 合入 `main` 前最终确认 |

#### 下午 Milestone

- 发布候选版本冻结
- 完成彩排与正式交付

#### 下午 Checkpoints

| 时间 | Checkpoint | 输出物 |
|---|---|---|
| 14:00 | 发布冻结 | 停止新功能提交，仅允许 hotfix |
| 16:00 | 最终演示彩排 | 按演示脚本完成全流程走查 |
| 18:00 | 正式交付 | `main` 发布、归档已知问题、输出复盘 |

### 4.6 代码 Merge 节奏建议

| 节奏 | 规则 |
|---|---|
| 每天中午 | 合并半天稳定成果到 `develop` |
| 每天下午/晚上 | 合并联调修复和当日主成果到 `develop` |
| Day 3 晚上 | 生成 `release/day3-rc`，开始预发布验证 |
| Day 4 中午 | 生成 `release/day4-rc`，准备正式发布 |
| Day 4 晚上 | `release/day4-rc` 合并到 `main`，完成交付 |

---

## 5. 风险提示与阻碍预案

### 5.1 范围失控风险

- 风险：团队容易把时间耗在 P1 体验增强和非关键功能上
- 预案：
  - 每晚收口会只问一个问题：`不做这个功能，是否阻塞端到端演示？`
  - 若不阻塞，则立即降级
  - Team Lead 必须拥有最终砍需求权

### 5.2 Git 冲突和集成失败风险

- 风险：多人并发开发同一页面、同一接口文件、同一配置目录时容易冲突
- 预案：
  - 前端按页面分工，后端按服务分工，减少同文件编辑
  - 共享契约放在 `shared/openapi` 与 `shared/schemas`，禁止私自改字段
  - 每半天合并一次，避免大分支长期漂移
  - 若接口字段要变，先更新契约再编码
  - 遇到跨模块冲突，优先由 Team Lead 统一裁决，不允许多人反复 rebasing 互相覆盖

### 5.3 训练链路成为总瓶颈风险

- 风险：真实训练耗时长，设备不稳定，日志与指标延迟高
- 预案：
  - 优先拆分成“任务编排”和“训练执行”两层
  - 先打通状态流和指标展示，再补真实训练
  - 统一使用小样本演示数据集，确保 3 到 5 分钟内可出结果

### 5.4 Agent 过度设计风险

- 风险：容易把 Agent 做成复杂编排系统，严重拖期
- 预案：
  - 只实现最小能力：
    - 1 个模板
    - 1 个工具绑定入口
    - 1 个聊天页
    - 1 个工具调用结果展示区
  - 不做工作流画布，不做多 Agent，不做复杂记忆系统

### 5.5 测试滞后风险

- 风险：测试如果 Day 3 才开始介入，会在最后一天集中爆雷
- 预案：
  - Day 1 即基于 Mock 编写冒烟用例
  - Day 2 开始做真实接口回归
  - Day 3 上午必须完成第一次完整 E2E 演练
  - 每晚输出阻塞缺陷 Top 5

### 5.6 环境不一致风险

- 风险：本地依赖、GPU、路径、配置不一致导致“我这边跑不起来”
- 预案：
  - Day 1 必须交付：
    - `.env.example`
    - 初始化脚本
    - 样例数据
    - 启动文档
  - 演示环境提前锁定，不在 Day 4 临时更换机器和依赖

### 5.7 Team Lead 管理建议

- 只盯三件事：范围、契约、联调
- 所有会议控制在 15 分钟内，避免“讨论型管理”
- 任何任务必须有唯一 owner，不允许多人共同负责一个交付物
- 所有状态同步以看板和接口契约为准，不依赖口头确认
- 交付目标必须始终围绕 `P0 主链路可演示`，而不是“功能点数量最大化”

---

## 附：推荐演示主链路

### 场景 A：图像分类

1. 上传眼底图像数据集
2. 预览图片和标签
3. 执行基础清洗与 EDA
4. 选择 `ResNet-18` 或 `ResNet-34`
5. 启动单任务训练
6. 查看训练曲线和日志
7. 在线测试单张图像
8. 在 Agent 对话中调用模型返回分级结果

### 场景 B：表格回归/分类

1. 上传 CSV 数据集
2. 预览字段和缺失值情况
3. 执行缺失值处理、异常值处理与数据集划分
4. 选择 `MLP`
5. 配置超参数并训练
6. 查看评估结果
7. 在线输入特征完成预测
8. 在 Agent 中通过自然语言调用预测工具
