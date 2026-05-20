"""SSE streaming chat engine with tool-call loop."""

from __future__ import annotations

import json
import uuid
from typing import Any, AsyncIterator

from app.core.config import settings
from app.core.errors import AppError, ERR_AGENT_CHAT_FAILED, ERR_AGENT_TOOL_ROUND_LIMIT
from src.agent.llm_provider import get_llm_provider
from src.agent.repository import AgentRepository
from src.agent.tool_wrapper import ToolWrapper
from shared.protocols import ChatRole, SSEEvent, SSEEventType


class ChatEngine:
    def __init__(self, repo: AgentRepository, tool_wrapper: ToolWrapper) -> None:
        self._repo = repo
        self._tool_wrapper = tool_wrapper

    async def chat(
        self,
        agent_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_message: str,
        system_prompt: str | None = None,
        model_config: dict[str, Any] | None = None,
    ) -> AsyncIterator[SSEEvent]:
        """Run a multi-turn chat with tool-call loop, yielding SSE events."""
        # Persist user message
        self._repo.add_message(
            conversation_id=conversation_id,
            role=ChatRole.USER,
            content=user_message,
        )
        self._repo.commit()

        # Build message history
        history = self._repo.get_messages(
            conversation_id, limit=settings.agent_max_history_messages
        )
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        for msg in history:
            messages.append({"role": msg.role.value, "content": msg.content})

        # Get tool schemas
        tools_schema = self._tool_wrapper.get_tools_schema(agent_id)

        # Select LLM provider
        provider = (model_config or {}).get("provider", settings.llm_default_provider)
        model = (model_config or {}).get("model", settings.llm_default_model)
        llm = get_llm_provider(
            provider,
            api_key=settings.llm_api_key,
            api_base=settings.llm_api_base,
            model=model,
        )

        # Tool-call loop
        assistant_content = ""
        tool_calls_log: list[dict[str, Any]] = []
        max_rounds = settings.agent_max_tool_rounds

        for round_idx in range(max_rounds + 1):
            if round_idx == max_rounds:
                yield SSEEvent(
                    type=SSEEventType.ERROR,
                    content=f"Exceeded max tool call rounds ({max_rounds})",
                )
                break

            round_had_tool_call = False

            try:
                async for event in llm.chat(
                    messages=messages,
                    tools=tools_schema or None,
                ):
                    if event.type == SSEEventType.TOKEN:
                        assistant_content += event.content or ""
                        yield event

                    elif event.type == SSEEventType.TOOL_CALL:
                        round_had_tool_call = True
                        yield event

                        # Execute tool
                        result = await self._tool_wrapper.call_tool(
                            agent_id, event.name, event.args or {}
                        )
                        yield SSEEvent(
                            type=SSEEventType.TOOL_RESULT,
                            name=event.name,
                            result=result,
                        )

                        # Append to message history for next LLM call
                        tool_calls_log.append({
                            "name": event.name,
                            "args": event.args,
                            "result": result,
                        })
                        messages.append({"role": "assistant", "content": ""})
                        messages.append({
                            "role": "tool",
                            "content": json.dumps(result, ensure_ascii=False),
                            "name": event.name,
                        })
                        break  # Re-invoke LLM with tool result

                    elif event.type == SSEEventType.ERROR:
                        yield event
                        break

                    elif event.type == SSEEventType.DONE:
                        yield event
                        # Persist assistant message
                        self._repo.add_message(
                            conversation_id=conversation_id,
                            role=ChatRole.ASSISTANT,
                            content=assistant_content,
                            tool_calls=tool_calls_log if tool_calls_log else None,
                        )
                        self._repo.commit()
                        return

                else:
                    # Generator exhausted without DONE
                    break

                if not round_had_tool_call:
                    break

            except Exception as exc:
                yield SSEEvent(type=SSEEventType.ERROR, content=str(exc))
                break

        # Fallback: persist whatever we have
        if assistant_content or tool_calls_log:
            self._repo.add_message(
                conversation_id=conversation_id,
                role=ChatRole.ASSISTANT,
                content=assistant_content or "(tool call only)",
                tool_calls=tool_calls_log if tool_calls_log else None,
            )
            self._repo.commit()
