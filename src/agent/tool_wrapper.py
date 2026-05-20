"""Model → OpenAI function-calling tool wrapper."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.errors import AppError, ERR_AGENT_TOOL_BIND_FAILED, ERR_AGENT_TOOL_NOT_FOUND
from src.agent.repository import AgentRepository
from shared.protocols import ToolType


class ToolWrapper:
    def __init__(self, repo: AgentRepository) -> None:
        self._repo = repo

    def get_tools_schema(self, agent_id: uuid.UUID) -> list[dict[str, Any]]:
        """Generate OpenAI function-calling compatible tools param for all bound tools."""
        tools = self._repo.list_tools(agent_id)
        if not tools:
            return []
        return [self._tool_to_openai_schema(t) for t in tools]

    def _tool_to_openai_schema(self, tool: Any) -> dict[str, Any]:
        desc = tool.description
        if not desc and tool.model_id:
            desc = f"使用绑定的模型进行推理"

        config = tool.config or {}
        params_schema = config.get("params_schema", {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "模型输入数据"},
            },
            "required": ["input"],
        })

        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": desc or f"调用工具 {tool.name}",
                "parameters": params_schema,
            },
        }

    async def call_tool(
        self,
        agent_id: uuid.UUID,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Execute a tool call — route by tool type."""
        tools = self._repo.list_tools(agent_id)
        tool = next((t for t in tools if t.name == tool_name), None)
        if not tool:
            raise AppError.not_found(
                f"Tool '{tool_name}' not found", code=ERR_AGENT_TOOL_NOT_FOUND
            )

        tool_type = tool.type.value if hasattr(tool.type, "value") else str(tool.type)

        if tool_type == ToolType.MODEL_INFERENCE.value:
            return await self._call_model_inference(tool, arguments)
        elif tool_type == ToolType.API_CALL.value:
            return {"error": "api_call tools not yet implemented"}
        else:
            return {"result": f"Custom tool '{tool_name}' executed (placeholder)"}

    async def _call_model_inference(self, tool: Any, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call online inference for a bound model.

        For now, returns a mock result since the real inference engine is still mock.
        When P8 ships real online_inference, this will call InferenceEngineProtocol.
        """
        model_id = str(tool.model_id) if tool.model_id else None
        input_data = arguments.get("input", "")

        # TODO: replace with real InferenceEngineProtocol.online_inference() when available
        return {
            "prediction": "mock_prediction",
            "confidence": 0.95,
            "model_id": model_id,
            "input_preview": input_data[:100] if input_data else "",
        }
