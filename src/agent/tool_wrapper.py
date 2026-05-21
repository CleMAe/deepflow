"""Model -> OpenAI function-calling tool wrapper."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from app.core.errors import ERR_AGENT_TOOL_NOT_FOUND, AppError
from shared.protocols import ToolType
from src.agent.repository import AgentRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.services.inference_service import InferenceService


class ToolWrapper:
    def __init__(
        self,
        repo: AgentRepository,
        inference_service: InferenceService | None = None,
        db: Session | None = None,
    ) -> None:
        self._repo = repo
        self._inference_service = inference_service
        self._db = db

    def get_tools_schema(self, agent_id: uuid.UUID) -> list[dict[str, Any]]:
        """Generate OpenAI function-calling compatible tools param for all bound tools."""
        tools = self._repo.list_tools(agent_id)
        if not tools:
            return []
        return [self._tool_to_openai_schema(t) for t in tools]

    def _tool_to_openai_schema(self, tool: Any) -> dict[str, Any]:
        desc = tool.description
        if not desc and tool.model_id:
            desc = "使用绑定的模型进行推理"

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

        Uses InferenceService when available; falls back to mock result.
        """
        model_id = str(tool.model_id) if tool.model_id else None
        input_data = arguments.get("input", "")

        if self._inference_service and model_id:
            if not self._db:
                return {"error": "Database session not available for inference", "model_id": model_id}

            project_id = None
            if hasattr(tool, "agent") and tool.agent is not None:
                project_id = tool.agent.project_id
            else:
                return {"error": f"Agent relationship not loaded for tool '{tool.name}', cannot determine project", "model_id": model_id}

            try:
                result = self._inference_service.online_inference(
                    db=self._db,
                    project_id=project_id,
                    model_id=uuid.UUID(model_id),
                    input_data=input_data,
                )
                return result.model_dump()
            except Exception as e:
                return {
                    "error": str(e),
                    "model_id": model_id,
                    "input_preview": input_data[:100] if isinstance(input_data, str) else str(input_data)[:100],
                }

        # Fallback: mock result when inference service not available
        return {
            "prediction": "mock_prediction",
            "confidence": 0.95,
            "model_id": model_id,
            "input_preview": input_data[:100] if isinstance(input_data, str) else str(input_data)[:100],
        }
