"""LLM provider layer — LiteLLM (real) and MockLLM (dev/test)."""

from __future__ import annotations

import json
import uuid
from typing import Any, AsyncIterator, Optional

from shared.protocols import SSEEvent, SSEEventType


class MockLLMProvider:
    """Returns preset replies when real LLM API is unavailable."""

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[SSEEvent]:
        if tools:
            tool_fn = tools[0]["function"]
            yield SSEEvent(
                type=SSEEventType.TOOL_CALL,
                name=tool_fn["name"],
                args={"input": "mock_input"},
            )
            yield SSEEvent(
                type=SSEEventType.TOOL_RESULT,
                name=tool_fn["name"],
                result={"prediction": "mock_result", "confidence": 0.9},
            )
            yield SSEEvent(type=SSEEventType.TOKEN, content="根据模型分析结果，这是一个测试回复。")
        else:
            yield SSEEvent(type=SSEEventType.TOKEN, content="我已收到您的请求，正在处理中。")

        yield SSEEvent(type=SSEEventType.DONE, message_id=str(uuid.uuid4()))


class LiteLLMProvider:
    """Calls LLM APIs via LiteLLM, compatible with OpenAI format."""

    def __init__(
        self,
        *,
        api_key: str = "",
        api_base: str = "",
    ) -> None:
        self._api_key = api_key
        self._api_base = api_base

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: str = "gpt-4",
    ) -> AsyncIterator[SSEEvent]:
        try:
            import litellm
        except ImportError:
            yield SSEEvent(type=SSEEventType.ERROR, content="litellm not installed")
            yield SSEEvent(type=SSEEventType.DONE, message_id=str(uuid.uuid4()))
            return

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if self._api_key:
            kwargs["api_key"] = self._api_key
        if self._api_base:
            kwargs["api_base"] = self._api_base
        if tools:
            kwargs["tools"] = tools

        msg_id = str(uuid.uuid4())
        current_tool_calls: dict[int, dict[str, Any]] = {}

        try:
            response = await litellm.acompletion(**kwargs)
            async for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue

                # Handle tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index if hasattr(tc, "index") else 0
                        if idx not in current_tool_calls:
                            current_tool_calls[idx] = {
                                "id": tc.id or "",
                                "name": "",
                                "arguments": "",
                            }
                        if tc.function:
                            if tc.function.name:
                                current_tool_calls[idx]["name"] = tc.function.name
                            if tc.function.arguments:
                                current_tool_calls[idx]["arguments"] += tc.function.arguments
                    continue

                # Handle text content
                if delta.content:
                    yield SSEEvent(type=SSEEventType.TOKEN, content=delta.content)

            # Emit completed tool calls
            for tc_data in current_tool_calls.values():
                args = {}
                if tc_data["arguments"]:
                    try:
                        args = json.loads(tc_data["arguments"])
                    except json.JSONDecodeError:
                        args = {"raw": tc_data["arguments"]}
                yield SSEEvent(
                    type=SSEEventType.TOOL_CALL,
                    name=tc_data["name"],
                    args=args,
                )

        except Exception as exc:
            yield SSEEvent(type=SSEEventType.ERROR, content=str(exc))

        yield SSEEvent(type=SSEEventType.DONE, message_id=msg_id)


def get_llm_provider(
    provider: str = "mock",
    *,
    api_key: str = "",
    api_base: str = "",
    model: str = "gpt-4",
) -> MockLLMProvider | LiteLLMProvider:
    if provider == "mock":
        return MockLLMProvider()
    return LiteLLMProvider(api_key=api_key, api_base=api_base)
