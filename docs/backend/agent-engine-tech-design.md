# DeepFlow Agent 引擎技术方案

> 作者：P1 夏镜萧（架构师 / Tech Lead）
> 日期：2026-05-20
> 状态：Draft → 待团队 Review

---

## 1. 概述

Agent 引擎是 DeepFlow 平台的最终交付模块，负责将训练好的模型封装为可调用工具，通过 LLM 对话 Agent 实现「对话即推理」的交互范式。

**核心能力：**

1. **Agent CRUD** — 创建/查询/更新/删除对话 Agent
2. **模型工具封装** — 将训练好的模型自动包装为 FastAPI 可调用端点
3. **SSE 流式对话** — Agent 与用户多轮对话，支持工具调用（function calling）
4. **Prompt 模板管理** — 系统提示词模板的保存、变量替换、列表查询
5. **对话历史** — 完整对话记录持久化，支持分页回溯

**关键约束（来自 PRD + API 契约）：**

- 对话通过 **SSE（Server-Sent Events）** 流式返回，不用 WebSocket
- 使用 **LiteLLM** 兼容 OpenAI API 格式，支持 `openai / anthropic / azure / mock` 四种 provider
- 若 LLM API 不可用，需实现 `MockLLM` 返回预设回复，保证工具调用链路可验证
- 模型工具封装输出 **OpenAI function-calling 兼容 schema**

---

## 2. 模块架构

```
src/
├── agent/
│   ├── __init__.py
│   ├── router.py             # FastAPI 路由（11 个端点）
│   ├── service.py            # Agent 业务逻辑编排
│   ├── schemas.py            # Pydantic 请求/响应模型
│   ├── repository.py         # DB 查询封装
│   ├── chat_engine.py        # SSE 对话引擎（核心）
│   ├── tool_wrapper.py       # 模型工具封装
│   ├── prompt_manager.py     # Prompt 模板管理
│   ├── llm_provider.py       # LLM 调用层（LiteLLM + MockLLM）
│   └── sse_types.py          # SSE 事件类型定义
└── infra/
    └── db/
        └── models/
            └── agent.py      # ✅ 已存在（Agent + AgentStatus）
```

**额外需要新增的 ORM 模型：**

| 模型 | 表名 | 说明 |
|------|------|------|
| `AgentTool` | `agent_tools` | Agent 绑定工具（多对多中间表） |
| `ChatMessage` | `chat_messages` | 对话消息持久化 |
| `PromptTemplate` | `prompt_templates` | Prompt 模板存储 |
| `Conversation` | `conversations` | 对话会话（可选，用于多轮分组） |

### 模块依赖关系

```
router.py
  ├── service.py ──→ repository.py (DB)
  ├── chat_engine.py ──→ llm_provider.py (LLM API)
  │                  └──→ tool_wrapper.py (工具调用)
  ├── prompt_manager.py ──→ repository.py
  └── tool_wrapper.py ──→ InferenceEngineProtocol (P7/P8)
                      └──→ ModelRegistryProtocol (P8)
```

**跨模块依赖（通过 Protocol 接口）：**

| 来源 | 接口 | 用途 |
|------|------|------|
| P8 | `InferenceEngineProtocol.online_inference()` | Agent 调用模型推理 |
| P8 | `ModelRegistryProtocol.get_model()` | 获取模型元信息，生成工具 schema |
| P6 | `AuthProtocol.verify_token()` | 验证用户身份 |

---

## 3. 核心数据模型

### 3.1 已有模型：Agent（无需修改）

```python
# src/infra/db/models/agent.py — 已存在
class Agent(Base):
    id: UUID
    project_id: UUID (FK → projects.id, CASCADE)
    name: str(256)
    description: str | None
    system_prompt: str | None
    model_config: JSONB     # {"provider": "openai", "model": "gpt-4", ...}
    tools: JSONB            # 冗余快照，工具绑定变更时同步更新
    status: AgentStatus     # active / inactive
    created_at, updated_at
```

### 3.2 新增模型：AgentTool

```python
class AgentTool(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_tools"

    agent_id: UUID (FK → agents.id, CASCADE)
    name: str(256)          # 工具调用名，如 "resnet50_predict"
    type: ToolType          # model_inference / api_call / custom
    model_id: UUID | None   # type=model_inference 时必填
    description: str | None # 工具描述（供 LLM function calling 使用）
    config: JSONB           # 端点配置：{"endpoint": "...", "params_schema": {...}}
```

### 3.3 新增模型：Conversation

```python
class Conversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversations"

    agent_id: UUID (FK → agents.id, CASCADE)
    project_id: UUID (FK → projects.id, CASCADE)
    title: str(256) | None  # 可选标题（取首条消息前 50 字）
```

### 3.4 新增模型：ChatMessage

```python
class ChatMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_messages"

    conversation_id: UUID (FK → conversations.id, CASCADE)
    role: ChatRole           # user / assistant / system / tool
    content: Text
    tool_calls: JSONB | None # LLM 发起的工具调用列表
    tool_call_id: str | None # 工具结果回传时的 ID
```

### 3.5 新增模型：PromptTemplate

```python
class PromptTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prompt_templates"

    agent_id: UUID (FK → agents.id, CASCADE)
    name: str(256)
    template: Text           # 支持 {{variable}} 模板语法
    description: str | None
    variables: JSONB         # ["context", "question"] — 变量名列表
```

---

## 4. SSE 对话引擎设计（核心）

### 4.1 对话流程

```
用户发送消息
    │
    ▼
┌─────────────────────┐
│  router.agent_chat() │  解析请求，校验 agent 存在且 active
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  chat_engine.chat()  │  构建消息历史 + 系统提示词
└────────┬────────────┘
         │
         ▼
┌──────────────────────────────┐
│  llm_provider.chat()         │  调用 LiteLLM / MockLLM
│  (async generator)           │  传入 tools 参数（function schemas）
└────────┬─────────────────────┘
         │
         ├── SSEEvent(type=token) ──→ yield 给客户端
         ├── SSEEvent(type=tool_call) ──→ 暂存，yield 给客户端
         │   │
         │   ▼
         │   tool_wrapper.call_tool(name, args) ──→ 调用推理
         │   │
         │   ▼
         │   SSEEvent(type=tool_result) ──→ 回传 LLM，yield 给客户端
         │   │
         │   ▼
         │   LLM 继续生成 ──→ 回到 token 流
         │
         └── SSEEvent(type=done) ──→ 持久化完整对话，yield 结束
```

### 4.2 SSE 事件协议

遵循 `src/shared/protocols.py` 中的 `SSEEventType` 枚举：

| 事件类型 | 字段 | 说明 |
|----------|------|------|
| `token` | `content` | 流式文本片段 |
| `tool_call` | `name`, `args` | LLM 请求调用工具 |
| `tool_result` | `name`, `result` | 工具执行结果回传 |
| `done` | `message_id` | 流结束，携带消息 ID |
| `error` | `content` | 错误信息 |

**SSE 输出格式：**

```
data: {"type": "token", "content": "根据"}

data: {"type": "token", "content": "模型推理结果"}

data: {"type": "tool_call", "name": "resnet50_predict", "args": {"image_url": "..."}}

data: {"type": "tool_result", "name": "resnet50_predict", "result": {"prediction": "cat", "confidence": 0.95}}

data: {"type": "token", "content": "该图片是一只猫，置信度 95%。"}

data: {"type": "done", "message_id": "a1b2c3d4-..."}
```

### 4.3 工具调用循环

当 LLM 返回 `tool_calls` 时，引擎进入工具调用循环：

```python
async def chat(self, messages, tools, ...) -> AsyncIterator[SSEEvent]:
    while True:
        async for event in self.llm_provider.chat(messages, tools, ...):
            yield event
            if event.type == SSEEventType.TOOL_CALL:
                # 执行工具
                result = await self.tool_wrapper.call_tool(event.name, event.args)
                yield SSEEvent(type=SSEEventType.TOOL_RESULT, name=event.name, result=result)
                # 将工具结果追加到消息历史，继续对话
                messages.append({"role": "tool", "name": event.name, "content": json.dumps(result)})
                break  # 重新调用 LLM
            elif event.type == SSEEventType.DONE:
                return  # 对话结束
```

设置最大工具调用轮次（默认 5 次）防止无限循环。

---

## 5. LLM 调用层设计

### 5.1 LiteLLM Provider（真实调用）

```python
class LiteLLMProvider:
    """通过 LiteLLM 调用各种 LLM API，兼容 OpenAI 格式。"""

    def __init__(self):
        self.client = AsyncOpenAI()  # LiteLLM 代理

    async def chat(self, messages, tools=None, temperature=0.7, max_tokens=2048):
        response = await litellm.acompletion(
            model=f"{provider}/{model}",  # e.g. "openai/gpt-4"
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in response:
            # 解析 chunk → SSEEvent
            ...
```

### 5.2 MockLLM Provider（开发/测试）

```python
class MockLLMProvider:
    """LLM API 不可用时的 Mock 实现，保证工具调用链路可验证。"""

    PRESET_RESPONSES = {
        "default": "我已收到您的请求，正在处理中。",
        "tool_call": "让我调用模型来帮您分析。",
    }

    async def chat(self, messages, tools=None, ...):
        # 如果有工具可用，模拟一次工具调用
        if tools:
            tool = tools[0]
            yield SSEEvent(type=SSEEventType.TOOL_CALL, name=tool["function"]["name"], args={"input": "mock"})
            yield SSEEvent(type=SSEEventType.TOOL_RESULT, name=tool["function"]["name"], result={"prediction": "mock_result", "confidence": 0.9})
            yield SSEEvent(type=SSEEventType.TOKEN, content="根据模型分析结果，这是一个测试回复。")
        else:
            yield SSEEvent(type=SSEEventType.TOKEN, content=self.PRESET_RESPONSES["default"])

        yield SSEEvent(type=SSEEventType.DONE, message_id=str(uuid4()))
```

**切换逻辑：** 在 `service.py` 中根据 `settings.mock_mode` 或 Agent 的 `model_config.provider == "mock"` 选择 Provider。

### 5.3 新增配置项

在 `src/infra/config.py` 中新增：

```python
# LLM / Agent
llm_default_provider: str = "mock"          # openai / anthropic / azure / mock
llm_default_model: str = "gpt-4"
llm_api_key: str = ""                       # 通过环境变量 LLM_API_KEY 注入
llm_api_base: str = ""                      # 自定义 API base URL（可选）
agent_max_tool_rounds: int = 5              # 单次对话最大工具调用轮次
agent_max_history_messages: int = 50        # 对话历史最大消息数（防止 token 溢出）
```

---

## 6. 模型工具封装设计

### 6.1 工具 Schema 生成

当 Agent 绑定模型工具时，`tool_wrapper.py` 自动生成 OpenAI function-calling 兼容 schema：

```python
def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
    """生成 OpenAI function-calling 兼容的 tools 参数。"""
    tool = self._get_tool(tool_name)
    if tool.type == ToolType.MODEL_INFERENCE:
        model_info = self.model_registry.get_model(tool.model_id)
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or f"使用 {model_info['arch_type']} 模型进行推理",
                "parameters": model_info.get("input_schema", {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "模型输入数据"},
                    },
                    "required": ["input"],
                }),
            },
        }
```

### 6.2 工具调用执行

```python
async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
    """执行工具调用 — 根据工具类型路由。"""
    tool = self._get_tool(tool_name)

    if tool.type == ToolType.MODEL_INFERENCE:
        # 调用在线推理
        result = self.inference_engine.online_inference(
            model_id=str(tool.model_id),
            input_data=arguments.get("input"),
            checkpoint_path=tool.config.get("checkpoint_path"),
        )
        return {
            "prediction": result.prediction,
            "confidence": result.confidence,
            "latency_ms": result.latency_ms,
        }
    elif tool.type == ToolType.API_CALL:
        # 外部 API 调用
        ...
    elif tool.type == ToolType.CUSTOM:
        # 自定义工具
        ...
```

### 6.3 工具绑定流程

```
POST /agents/{agent_id}/tools/bind
{
  "tools": [
    {
      "name": "resnet50_predict",
      "type": "model_inference",
      "model_id": "uuid-of-model",
      "description": "使用 ResNet-50 模型对图片进行分类预测"
    }
  ]
}
```

后端处理：
1. 校验 `model_id` 存在且属于当前项目
2. 调用 `ModelRegistryProtocol.get_model()` 获取模型元信息
3. 生成工具配置（endpoint、参数 schema）
4. 写入 `agent_tools` 表
5. 同步更新 `agents.tools` JSONB 冗余字段

---

## 7. Prompt 模板管理

### 7.1 模板语法

使用 Python `string.Template` 的安全子集（`$variable` 语法），避免 Jinja2 引入额外依赖：

```
你是一个专业的数据分析助手。当前数据集信息：
- 数据集名称：$dataset_name
- 行数：$row_count
- 列数：$column_count

请根据用户问题进行分析，必要时调用绑定工具。
```

### 7.2 变量提取

保存模板时自动提取变量：

```python
import re

def extract_variables(template: str) -> list[str]:
    return list(set(re.findall(r'\$(\w+)', template)))
```

### 7.3 模板渲染

```python
from string import Template

def render(template_str: str, variables: dict[str, str]) -> str:
    return Template(template_str).safe_substitute(variables)
```

---

## 8. API 端点实现计划

11 个端点，按优先级排序：

| # | 端点 | 方法 | 说明 | 优先级 |
|---|------|------|------|--------|
| 1 | `/projects/{id}/agents` | GET | Agent 列表（分页） | P0 |
| 2 | `/projects/{id}/agents` | POST | 创建 Agent | P0 |
| 3 | `/projects/{id}/agents/{agent_id}` | GET | Agent 详情 | P0 |
| 4 | `/projects/{id}/agents/{agent_id}` | PUT | 更新 Agent | P0 |
| 5 | `/projects/{id}/agents/{agent_id}` | DELETE | 删除 Agent | P0 |
| 6 | `/projects/{id}/agents/{agent_id}/tools/bind` | POST | 绑定工具 | P0 |
| 7 | `/projects/{id}/agents/{agent_id}/tools` | GET | 已绑定工具列表 | P0 |
| 8 | `/projects/{id}/agents/{agent_id}/chat` | POST | SSE 流式对话 | P0 |
| 9 | `/projects/{id}/agents/{agent_id}/chat/history` | GET | 对话历史 | P0 |
| 10 | `/projects/{id}/agents/{agent_id}/prompts` | POST | 保存 Prompt 模板 | P1 |
| 11 | `/projects/{id}/agents/{agent_id}/prompts` | GET | Prompt 模板列表 | P1 |

---

## 9. 对话历史持久化策略

### 9.1 写入时机

对话消息**不在 SSE 流式过程中逐条写入 DB**，而是在流结束后批量写入，避免流式过程中的 DB 写入延迟影响 SSE 推送性能。

```
SSE 流进行中：
  → 消息暂存在内存（asyncio.Queue 或 list）
  → 实时 yield SSE 事件

SSE 流结束（收到 done/error）：
  → 批量将完整消息写入 DB
  → 包括：用户消息 + 助手回复 + 工具调用/结果
```

### 9.2 对话上下文构建

GET 请求对话历史时，从 `chat_messages` 表查询并按 `created_at` 排序。构建 LLM 输入时，截取最近 N 条消息（`agent_max_history_messages` 配置），超出时保留 system prompt + 最近 N 条。

---

## 10. 错误码规划

| 错误码 | 含义 | 触发场景 |
|--------|------|----------|
| 70-1-1 | ERR_AGENT_INVALID_STATUS | 对 inactive Agent 发起对话 |
| 70-2-1 | ERR_AGENT_NOT_FOUND | Agent ID 不存在 |
| 70-2-2 | ERR_AGENT_TOOL_NOT_FOUND | 绑定工具不存在 |
| 70-3-1 | ERR_AGENT_FORBIDDEN | 无权操作该 Agent |
| 70-4-1 | ERR_AGENT_TOOL_BIND_FAILED | 工具绑定失败（model_id 不存在等） |
| 70-4-2 | ERR_AGENT_CHAT_FAILED | 对话引擎异常（LLM 调用失败） |
| 70-4-3 | ERR_AGENT_TOOL_ROUND_LIMIT | 超过最大工具调用轮次 |
| 70-4-4 | ERR_AGENT_PROMPT_RENDER_FAILED | 模板变量缺失 |

---

## 11. 实施计划

### Phase 1：基础 CRUD（Day 3，预计 4h）

- [ ] 新增 4 个 ORM 模型 + Alembic migration
- [ ] 实现 `repository.py`（Agent / AgentTool / ChatMessage / PromptTemplate 查询）
- [ ] 实现 `schemas.py`（Pydantic 请求/响应模型）
- [ ] 实现 `service.py` CRUD 部分
- [ ] 实现 `router.py` 端点 1-7（CRUD + 工具绑定）
- [ ] 注册路由到 `src/app/api/v1/router.py`

### Phase 2：对话引擎（Day 3-4，预计 6h）

- [ ] 实现 `llm_provider.py`（LiteLLMProvider + MockLLMProvider）
- [ ] 实现 `chat_engine.py`（SSE 流 + 工具调用循环）
- [ ] 实现 `tool_wrapper.py`（schema 生成 + 工具执行）
- [ ] 实现 `router.py` 端点 8-9（对话 + 历史）
- [ ] 新增配置项到 `src/infra/config.py`

### Phase 3：Prompt 管理 + 联调（Day 4，预计 3h）

- [ ] 实现 `prompt_manager.py`
- [ ] 实现 `router.py` 端点 10-11
- [ ] 与 P5 前端 Agent 对话页联调 SSE 流式
- [ ] 与 P8 联调 InferenceEngineProtocol 接入

### Phase 4：测试 + 文档（Day 4-5，预计 2h）

- [ ] pytest 单元测试（service + chat_engine + tool_wrapper）
- [ ] MockLLM 端到端测试（覆盖工具调用完整链路）
- [ ] 更新 `openapi.yaml` 中 Agent 相关 schema（如有遗漏）

---

## 12. 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 对话传输协议 | SSE | API 契约已确定；SSE 比 WebSocket 更简单，单向推送足够 |
| LLM 调用库 | LiteLLM | 支持 OpenAI/Anthropic/Azure 多供应商，统一接口 |
| 工具 schema 格式 | OpenAI function-calling | LLM 生态主流格式，LiteLLM 原生支持 |
| 对话持久化时机 | 流结束后批量写入 | 避免流式过程中 DB 写入延迟影响 SSE |
| Prompt 模板语法 | `string.Template`（`$var`） | 轻量无额外依赖，避免 Jinja2 模板注入风险 |
| 工具调用防死循环 | 最大轮次限制（5 次） | 防止 LLM 反复调用工具无法收敛 |
| Agent.tools 冗余字段 | 保留 JSONB 快照 | 读取详情时避免 JOIN 查询，写入时同步更新 |
