# P5 Day2 开发日志：批量推理 + Agent 管理骨架

> 日期：2026-05-19  
> 角色：P5 FE Dev（推理 + Agent）  
> 分支：`feat/p5-day2-batch-agent`  
> 功能提交：`c421a2c feat(p5): add batch inference and agent management`  
> PR：<https://github.com/CleMAe/deepflow/pull/new/feat/p5-day2-batch-agent>

## 今日目标

完成 P5 Day2 范围：在 Day1 “模型评估 + 在线测试”基础上，补齐“批量推理”页面骨架，并实现 Agent 管理页骨架。继续使用 MSW Mock 作为前端独立验收依据，不接入真实 Agent 对话和 SSE 流式响应。

## 分支与主线同步

1. 基于最新 `origin/main` 开发 Day2
   - 当前 Day2 分支：`feat/p5-day2-batch-agent`。
   - 已执行 `git pull --rebase origin main`，同步主分支代码质量修复。
   - Rebase 无冲突。

2. 当前 Git 状态
   - 已同步最新 `origin/main`，无 behind。
   - PR 分支包含 Day2 功能提交和本文档提交。
   - 工作区干净。

## 完成内容

1. 批量推理 API 封装
   - 更新 `frontend/src/api/inference.ts`。
   - 新增 OpenAPI 类型导出：
     - `BatchInferenceRequest`
     - `InferenceTask`
   - 新增接口封装：
     - `POST /projects/{projectId}/inference/batch`
     - `GET /projects/{projectId}/inference/{taskId}`

2. 批量推理页面骨架
   - 更新 `frontend/src/pages/ProjectInferencePage.tsx`。
   - 在推理测试页新增 “批量推理” Tab。
   - 支持选择模型、数据集和输出格式。
   - 提交后启动批量推理任务。
   - 使用 React Query 轮询任务状态。
   - 展示任务 ID、模型、数据集、结果路径、进度条和预测结果预览表。

3. Agent API 封装
   - 新增 `frontend/src/api/agents.ts`。
   - 封装 Agent 管理相关接口：
     - `GET /projects/{projectId}/agents`
     - `POST /projects/{projectId}/agents`
     - `PUT /projects/{projectId}/agents/{agentId}`
     - `DELETE /projects/{projectId}/agents/{agentId}`
     - `POST /projects/{projectId}/agents/{agentId}/tools/bind`
     - `GET /projects/{projectId}/agents/{agentId}/tools`

4. Agent 管理页骨架
   - 替换 `frontend/src/pages/ProjectAgentsPage.tsx` 占位内容。
   - 页面入口：`/projects/:projectId/agents`。
   - 支持 Agent 列表展示。
   - 支持创建 Agent。
   - 支持删除 Agent。
   - 支持为 Agent 绑定模型推理工具。
   - 展示 Agent 数量、绑定工具数量和 Mock 数据来源。

5. MSW Mock
   - 扩展 `frontend/src/mocks/handlers/inference.ts`：
     - `POST /api/v1/projects/:projectId/inference/batch`
     - `GET /api/v1/projects/:projectId/inference/:taskId`
   - 新增 `frontend/src/mocks/handlers/agents.ts`：
     - Agent 列表
     - Agent 创建
     - Agent 更新
     - Agent 删除
     - Agent 工具列表
     - Agent 工具绑定
   - 更新 `frontend/src/mocks/browser.ts` 注册 Agent handlers。

6. P5 API 响应解包
   - 保持 `frontend/src/lib/axios.ts` 与主分支一致，不改变全局拦截器行为。
   - 在 `frontend/src/api/inference.ts` 和 `frontend/src/api/agents.ts` 内部解包 OpenAPI 标准响应 `{ code, message, data }`。
   - 避免影响登录、项目列表、数据集列表等已有页面的数据访问约定。

## 契约对齐

1. 推理接口
   - 批量推理请求体使用 OpenAPI 中的 `BatchInferenceRequest`。
   - 批量推理结果使用 OpenAPI 中的 `InferenceTask`。
   - 在线测试继续使用 Day1 修正后的 `input_data` 字段。

2. Agent 接口
   - 创建 Agent 使用 `AgentCreate`。
   - 工具绑定使用 `ToolBindRequest`，请求体为 `tools[]`。
   - 工具类型使用 `model_inference`。

3. 范围控制
   - Day2 只实现“批量推理页 + Agent 管理页骨架”。
   - 未实现 Agent 对话、SSE 流式响应、Prompt 编辑器和对话日志。

## 验证结果

已通过：

```bash
npm run lint
npx tsc -b
npm run test
npx -p node@20.19.0 node ./node_modules/vite/bin/vite.js build
```

测试结果：

```text
2 个测试文件通过
4 个测试用例通过
```

构建结果：

```text
Vite production build 通过
仅存在 chunk 体积 warning，不阻塞 PR
```

本地页面验证入口：

```text
http://127.0.0.1:5173/projects/proj-1/inference
http://127.0.0.1:5173/projects/proj-1/agents
```

## 遇到的问题

1. 本机 Node 版本偏低
   - 当前版本：`v20.15.0`。
   - Vite 要求：`20.19+` 或 `22.12+`。
   - 处理方式：继续使用 `npx -p node@20.19.0` 执行 production build。
   - 建议：团队统一升级到 Node `20.19.0+`。

2. Windows optional dependency 缺失
   - Vite/Rolldown 与 Lightning CSS 在本地构建时依赖 Windows 原生 optional package。
   - 本地通过 `npm install --no-save` 补齐缺失包后构建通过。
   - 未改动 `frontend/package.json` 或 `frontend/package-lock.json`。

3. 真实后端接口尚未联调
   - 当前 Day2 验收仍基于 MSW Mock。
   - 后续切换真实 API 时，需要重点确认批量任务状态推进、Agent 工具绑定返回结构和错误码。

## 未完成内容

以下内容不属于 Day2 范围，暂未实现：

- Agent 对话页
- SSE 流式响应
- Prompt 编辑器
- 对话日志页
- ONNX 导出页面
- ROC/PR 曲线
- 批量推理真实后端联调

## Day3 建议

1. Agent 对话页
   - 实现 Chat UI。
   - 接入 `POST /agents/{agent_id}/chat`。
   - 支持流式内容逐步渲染。

2. Agent 工具调用联调
   - 与 P1 确认工具调用事件格式。
   - 与 P7/P8 确认模型推理工具的真实输入输出。
   - 完成一次 Agent 调用模型工具的端到端链路。

3. 从 Mock 切换真实 API
   - 优先联调批量推理任务启动和结果轮询。
   - 确认 Agent 列表、创建、工具绑定接口契约是否与 OpenAPI 完全一致。

## 当前状态

P5 Day2 范围已完成，可作为前端独立 Mock 验收版本提交 PR。后续重点进入 Day3 Agent 对话和真实接口联调。
