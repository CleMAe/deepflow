# P5 Day4 开发日志：对话日志 + Prompt 编辑器 + Agent 页面打磨

> 日期：2026-05-21  
> 角色：P5 FE Dev（推理 + Agent）  
> 分支：`feat/p5-day4-agent-prompt-history`  
> 功能提交：`207884c 完成P5 Day4 Agent日志与Prompt收尾`  
> PR：<https://github.com/CleMAe/deepflow/pull/new/feat/p5-day4-agent-prompt-history>

## 今日目标

完成 P5 Day4 收尾交付范围：在 Day3 Agent 对话工作区基础上，补齐“对话日志”入口，增强 Prompt 编辑器体验，并对 Agent 管理页面进行字体排版和信息显示优化。继续保留 MSW Mock，保证真实后端未稳定联调时前端仍可独立验收。

## 分支与主线同步

1. 基于最新 `origin/main` 开发 Day4
   - 当前分支：`feat/p5-day4-agent-prompt-history`。
   - 开始 Day4 前已从最新 `origin/main` 创建分支。
   - 开发过程中 `origin/main` 合入 PR #40：`fix/ci-lazy-torch-imports`。
   - 已通过 fast-forward 同步到 `a54f210`，无冲突。

2. 主线更新影响评估
   - PR #40 修改范围：
     - `backend/pytest.ini`
     - `src/engine/inference_engine.py`
   - 该更新属于后端 CI / 推理引擎懒加载修复，不影响 P5 前端 Agent 页面。
   - 同步后重新运行前端验证，结果通过。

3. 当前 Git 状态
   - 提交前相对 `origin/main`：`Ahead 0 / Behind 0`。
   - 本次 PR 仅包含 P5 Day4 前端文件和本开发日志。

## 完成内容

1. 对话日志页
   - 更新 `frontend/src/pages/ProjectAgentsPage.tsx`。
   - Agent 工作区新增 `对话日志` Tab。
   - 支持选择 Agent。
   - 支持输入 / 刷新 `conversation_id`。
   - 展示历史消息角色、时间、正文和工具调用参数 / 结果。
   - 支持显示当前会话消息数和会话 ID。

2. Agent API 封装增强
   - 更新 `frontend/src/api/agents.ts`。
   - 扩展 `getChatHistory`，支持：
     - `conversationId`
     - `page`
     - `pageSize`
   - 新增 `AgentChatHistory` 类型，兼容 OpenAPI 的 `items` 字段和后端当前返回的 `messages` 字段。
   - 扩展 SSE 事件类型，兼容 `conversation_id`。

3. Prompt 编辑器增强
   - Prompt 模板页升级为 `Prompt 编辑器`。
   - 支持变量自动提取：
     - 手动填写的变量列表
     - 模板中的 `$variable` 占位符
   - 支持变量预览区：
     - `prediction`
     - `confidence`
     - `context`
   - 支持实时渲染 Prompt 预览。
   - 支持从模板列表加载已有模板到编辑器。

4. Agent 管理页 UI 打磨
   - 优化 `管理` Tab 的字体层级、列宽和长文本展示。
   - Agent 表格使用固定列宽和横向滚动，减少长文本挤压。
   - Agent 名称 / 描述 / 模型 / Provider 支持省略和 tooltip。
   - 状态展示改为中文：
     - `启用`
     - `停用`
   - 工具标签改为紧凑显示，超过 3 个显示 `+N`。
   - 右侧概览数字突出显示。
   - 当前 Agent 卡片增加：
     - Provider
     - Temperature
     - Max Tokens
     - 系统提示词预览

5. MSW Mock 增强
   - 更新 `frontend/src/mocks/handlers/agents.ts`。
   - 新增 Mock 对话历史状态 `mockChatMessages`。
   - Mock SSE 对话完成后写入历史消息。
   - `GET /api/v1/projects/:projectId/agents/:agentId/chat/history` 支持：
     - `conversation_id`
     - `page`
     - `page_size`
   - Mock 响应同时返回 `items` 和 `messages`，兼容前端和后端当前差异。

## 契约对齐

1. Chat History
   - OpenAPI 当前定义 `PaginatedChatHistory.items`。
   - 后端 `src/agent/router.py` 当前返回 `ChatHistoryOut.messages`，并要求 `conversation_id`。
   - 前端临时兼容两种字段，降低联调风险。

2. Chat SSE
   - 前端继续使用 `fetch` + `ReadableStream` 解析 `POST /agents/{agent_id}/chat`。
   - 若 SSE 返回 `conversation_id`，前端自动更新当前会话 ID。
   - 为避免真实后端 UUID 校验失败，前端只在 `conversation_id` 为 UUID 时随聊天请求发送；Mock 默认 ID 仍可用于日志验收。

3. Prompt 模板
   - 保存模板继续使用 OpenAPI 中的 `PromptTemplateCreate`。
   - Day4 只实现前端编辑、加载和预览，不新增后端契约。

## 验证结果

已通过：

```bash
npm run lint
npx tsc -b
npx -p node@20.19.0 node ./node_modules/vitest/vitest.mjs run
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
http://127.0.0.1:5173/projects/proj-1/agents
```

## 遇到的问题

1. 主线开发过程中再次更新
   - `origin/main` 合入 PR #40。
   - 已同步并评估影响范围，主线更新不涉及 P5 前端文件。

2. Chat History 前后端字段不完全一致
   - OpenAPI 写的是 `items`。
   - 后端当前实现返回 `messages`。
   - 前端采用兼容读取：优先 `messages`，回退 `items`。

3. `conversation_id` 的 Mock 与真实后端校验差异
   - Mock 使用 `conversation-mock-1` 便于验收。
   - 真实后端要求 UUID。
   - 前端对聊天请求做 UUID 判断，避免把 Mock ID 发送给真实后端。

4. 本机 Node 版本偏低
   - 当前本机 Node 版本低于 Vite 要求。
   - 继续使用 `npx -p node@20.19.0` 执行测试和构建。

## 未完成内容

以下内容不属于 Day4 本次 PR 范围，暂未实现：

- Prompt 模板编辑 / 删除真实接口
- 后端 `/prompts/{prompt_id}/render` 的真实渲染接口接入
- 多会话列表选择
- Agent 调用真实模型工具的端到端业务验收
- 大 chunk 代码拆分优化

## 后续建议

1. 与 P1 对齐 Chat History 契约
   - 统一返回字段使用 `items` 或 `messages`。
   - 明确是否需要会话列表接口。

2. 与 P1/P8 做 Agent 工具链端到端联调
   - 验证 Agent 工具调用真实推理接口。
   - 确认 tool_call / tool_result 的字段稳定性。

3. 完善 Prompt 管理
   - 增加编辑、删除和后端 render 预览。
   - 若后端暂不提供 render，可保留前端本地预览作为 fallback。

## 当前状态

P5 Day4 对话日志、Prompt 编辑器增强和 Agent 管理页 UI 打磨已完成，可提交 PR 进入最终收尾评审。
