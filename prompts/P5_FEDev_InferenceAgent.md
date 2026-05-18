# P5 - 前端开发（推理 + Agent）提示词

## 角色定位

你负责 DeepFlow 的模型推理和 Agent 构建页面开发，对接后端 P1（Agent）和 P7/P8（推理）的 API。

## 你负责的页面

| 页面 | 核心功能 |
|------|---------|
| 模型评估页 | 评测指标展示、混淆矩阵热力图、ROC/PR 曲线 |
| 批量推理页 | 数据集选择、进度跟踪、结果预览 |
| 在线测试页 | 交互式输入、即时推理结果 |
| Agent 管理页 | Agent 列表、创建、工具绑定 |
| Agent 对话页 | Chat UI、多轮对话、SSE 流式响应、Prompt 编辑器 |
| 对话日志页 | 完整对话记录、回溯分析 |

## 你调用的接口

### 推理接口（来自 P7/P8）

```
POST   /api/v1/projects/{id}/inference/evaluate    # 模型评估
POST   /api/v1/projects/{id}/inference/batch       # 批量推理
GET    /api/v1/projects/{id}/inference/{task_id}   # 推理结果
POST   /api/v1/projects/{id}/inference/online      # 在线测试（单条）
POST   /api/v1/projects/{id}/inference/export-onnx # 导出 ONNX
```

### Agent 接口（来自 P1）

```
GET    /api/v1/projects/{id}/agents                         # Agent 列表
POST   /api/v1/projects/{id}/agents                         # 创建 Agent
GET    /api/v1/projects/{id}/agents/{agent_id}              # Agent 详情
PUT    /api/v1/projects/{id}/agents/{agent_id}              # 更新 Agent
DELETE /api/v1/projects/{id}/agents/{agent_id}              # 删除 Agent
POST   /api/v1/projects/{id}/agents/{agent_id}/tools/bind   # 绑定模型工具
POST   /api/v1/projects/{id}/agents/{agent_id}/chat         # 对话（SSE 流式）
GET    /api/v1/projects/{id}/agents/{agent_id}/chat/history # 对话历史
POST   /api/v1/projects/{id}/agents/{agent_id}/prompts      # 保存 Prompt 模板
GET    /api/v1/projects/{id}/agents/{agent_id}/prompts      # Prompt 模板列表
GET    /api/v1/projects/{id}/agents/{agent_id}/tools        # 已绑定工具列表
```

### 你还需要调用的辅助接口

```
# 选择推理用数据集（P7）
GET    /api/v1/projects/{id}/datasets
# 选择推理用模型（P8）
GET    /api/v1/projects/{id}/models
GET    /api/v1/projects/{id}/training-jobs/{job_id}         # 获取训练好的模型信息
```

## 关键交互说明

### Agent 对话 SSE 流式

`POST /api/v1/projects/{id}/agents/{agent_id}/chat` 返回 SSE 流：

```
Content-Type: text/event-stream

data: {"type": "content", "text": "根据模型推理结果..."}
data: {"type": "tool_call", "tool": "model_predict", "args": {...}}
data: {"type": "tool_result", "result": {...}}
data: {"type": "done", "message_id": "xxx"}
```

前端用 `EventSource` 或 `fetch` + `ReadableStream` 接收，逐字渲染到 Chat UI。

### 工具绑定流程

1. 用户创建 Agent → 选择 Prompt 模板
2. 从 `GET /agents/{agent_id}/tools` 查看已绑定工具
3. 调 `POST /agents/{agent_id}/tools/bind` 绑定模型工具（请求体：`{ model_id, tool_name, description }`）

### 批量推理流程

1. 选择数据集 + 模型 → `POST /inference/batch`
2. 返回 `task_id` → 轮询 `GET /inference/{task_id}` 查看进度和结果

## 接口请求/响应要点

- 在线测试请求体：`{ model_id, input: {...} }`，响应：`{ prediction, confidence, latency }`
- 评估请求体：`{ model_id, dataset_id, metrics: ["accuracy", "precision", "recall", "f1"] }`
- 混淆矩阵在评估响应的 `data.confusion_matrix` 字段，用 ECharts 热力图渲染
- 错误码：`60-XX-YYY`（推理）、`70-XX-YYY`（Agent）

## 技术栈

React 18, TypeScript, Ant Design 5.x, ECharts, React Query, MSW

## 开发顺序建议

1. Day1：推理评估页 + 在线测试页骨架（MSW mock）
2. Day2：批量推理页 + Agent 管理页骨架
3. Day3：Agent 对话页（接入真实 SSE）+ 工具绑定联调
4. Day3-4：对话日志页 + Prompt 编辑器 + UI 打磨
