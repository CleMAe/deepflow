# P5 Day3 开发日志：Agent 对话工作区 + SSE 接入

> 日期：2026-05-20  
> 角色：P5 FE Dev（推理 + Agent）  
> 分支：`feat/p5-day3-agent-chat`  
> 功能提交：`da00057 feat(p5): add agent chat workspace`  
> 日志提交：本文件提交后生成  
> PR：<https://github.com/CleMAe/deepflow/pull/new/feat/p5-day3-agent-chat>

## 今日目标

完成 P5 Day3 首轮范围：在 Day2 Agent 管理页基础上，补齐 Agent 对话工作区，接入 `POST /projects/{id}/agents/{agent_id}/chat` SSE 流式响应，并加入 Prompt 模板的前端入口。继续保留 MSW Mock fallback，保证真实后端未启动时前端可独立验收。

## 分支与主线同步

1. 基于最新 `origin/main` 开发 Day3
   - Day2 分支已合入 `main`，远端 Day2 分支已删除。
   - 从最新 `main` 创建 `feat/p5-day3-agent-chat`。
   - 开发后再次执行 `git pull --rebase origin main`，同步 P4 Day2 主线更新。
   - Rebase 无冲突。

2. 当前 Git 状态
   - 功能提交完成后，相对 `origin/main`：`Ahead 1 / Behind 0`。
   - 新增本开发日志后，分支将包含功能提交与日志提交。
   - 提交前已检查主线更新；若提交 PR 前 `origin/main` 再次变化，继续按流程 rebase 后验证。

## 完成内容

1. Agent API 扩展
   - 更新 `frontend/src/api/agents.ts`。
   - 新增 OpenAPI 类型导出：
     - `ChatRequest`
     - `ChatMessage`
     - `PaginatedChatHistory`
     - `PromptTemplate`
     - `PromptTemplateCreate`
   - 新增接口封装：
     - `GET /projects/{projectId}/agents/{agentId}/chat/history`
     - `GET /projects/{projectId}/agents/{agentId}/prompts`
     - `POST /projects/{projectId}/agents/{agentId}/prompts`
   - 新增 `streamAgentChat`，使用 `fetch` + `ReadableStream` 接收 `text/event-stream`。

2. Agent 页面工作区
   - 更新 `frontend/src/pages/ProjectAgentsPage.tsx`。
   - 将 Agent 页面扩展为三个 Tab：
     - `管理`
     - `对话`
     - `Prompt 模板`
   - 保留 Day2 的 Agent 列表、创建、删除、工具绑定能力。

3. Agent 对话 UI
   - 支持选择 Agent。
   - 支持输入消息并发送。
   - 支持流式追加 Agent 回复 token。
   - 支持停止生成。
   - 支持清空当前对话。
   - 支持展示当前 Agent 状态、LLM 模型和已绑定工具。

4. 工具调用事件展示
   - 对 SSE 事件进行前端解析。
   - 支持展示：
     - `token`
     - `content`
     - `tool_call`
     - `tool_result`
     - `error`
     - `done`
   - 在右侧工具调用面板展示工具名、调用参数和返回结果。

5. Prompt 模板入口
   - 支持保存 Prompt 模板。
   - 支持填写模板名称、描述、变量和模板内容。
   - 支持展示当前 Agent 的 Prompt 模板列表。
   - 为 Day3-4 的 Prompt 编辑器继续打基础。

6. MSW Mock fallback
   - 扩展 `frontend/src/mocks/handlers/agents.ts`。
   - 新增 Mock 接口：
     - `POST /api/v1/projects/:projectId/agents/:agentId/chat`
     - `GET /api/v1/projects/:projectId/agents/:agentId/chat/history`
     - `GET /api/v1/projects/:projectId/agents/:agentId/prompts`
     - `POST /api/v1/projects/:projectId/agents/:agentId/prompts`
   - Mock Chat 使用 `ReadableStream` 输出 SSE 格式数据，覆盖 token、工具调用、工具结果和 done 事件。

7. 主线 lint 基线修复
   - 更新 `frontend/src/components/p3-data/DataManagementView.tsx`。
   - 修复 React Hooks `preserve-manual-memoization` 规则报错。
   - 该问题来自最新主线，会阻塞 `npm run lint`，本次只做依赖数组的最小修复。

## 契约对齐

1. SSE 对话接口
   - 请求路径：`POST /projects/{projectId}/agents/{agentId}/chat`。
   - 请求体使用 OpenAPI 中的 `ChatRequest`。
   - 前端使用 `Accept: text/event-stream`。
   - 保留 `Authorization: Bearer <token>`。

2. SSE 事件兼容
   - P1 后端当前返回事件字段为：
     - `type`
     - `content`
     - `name`
     - `args`
     - `result`
     - `message_id`
   - 前端同时兼容提示词中的 `text` / `tool` 字段，降低后续联调变更成本。

3. Prompt 模板
   - 保存模板使用 OpenAPI 中的 `PromptTemplateCreate`。
   - 模板列表使用 `PromptTemplate[]`。

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
http://127.0.0.1:5173/projects/22222222-2222-2222-2222-222222222222/agents
```

## 遇到的问题

1. 主线更新频繁
   - Day3 开始后 `origin/main` 合入了 P4 Day2。
   - 当前分支已通过 rebase 同步最新主线。
   - P4 改动集中在训练页面和训练 mock，与 P5 Agent 页面无直接冲突。

2. `CLAUDE.md` 状态描述滞后
   - 文档中部分 Agent 状态仍写“未实现”。
   - 实际主线已包含 `src/agent/`、Agent router、SSE chat 和 Prompt 管理。
   - 本次实现以代码和 OpenAPI 契约为准。

3. SSE 对话无法使用 `EventSource`
   - 接口是 `POST`，浏览器原生 `EventSource` 只支持 `GET`。
   - 处理方式：使用 `fetch` + `ReadableStream` 解析 SSE。

4. 本机 Node 版本偏低
   - 当前版本：`v20.15.0`。
   - Vite 要求：`20.19+` 或 `22.12+`。
   - 处理方式：继续使用 `npx -p node@20.19.0` 执行 production build。
   - 建议：团队统一升级到 Node `20.19.0+`。

## 未完成内容

以下内容不属于本轮 Day3 首次提交，暂未完成：

- 对话日志独立页面
- Chat history 的完整会话选择与回放
- Prompt 模板编辑、删除和渲染预览
- Agent 对话与真实模型推理工具的端到端业务验收
- Agent 对话异常状态的更细粒度 UI

## 后续建议

1. 与 P1 联调真实 Agent SSE
   - 确认真实事件流是否稳定输出 `token`、`tool_call`、`tool_result`、`done`。
   - 确认 `message_id` 与 `conversation_id` 是否需要区分。

2. 完善对话日志
   - 基于 `GET /agents/{agent_id}/chat/history` 做会话回放。
   - 若后端需要 `conversation_id`，前端需要拿到并持久化当前会话 ID。

3. 完善 Prompt 管理
   - 增加模板编辑和删除。
   - 接入 `/prompts/{prompt_id}/render` 渲染预览接口。

4. 与 P8/P1 联调工具调用
   - 确认模型工具 schema。
   - 完成一次 Agent 调用模型推理工具的端到端链路。

## 当前状态

P5 Day3 首轮 Agent 对话工作区已完成，可作为前端独立 Mock 验收版本提交 PR。后续重点是与 P1 真实 Agent SSE 和 P8 推理工具进行联调。
