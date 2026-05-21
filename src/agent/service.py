"""Agent business logic — CRUD, tool binding, conversation management."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.errors import (
    ERR_AGENT_INVALID_STATUS,
    ERR_AGENT_NOT_FOUND,
    ERR_AGENT_TOOL_BIND_FAILED,
    AppError,
)
from shared.protocols import ToolType
from src.agent.repository import AgentRepository
from src.agent.schemas import AgentCreate, AgentUpdate, ToolBindItem
from src.infra.db.models import Agent
from src.infra.db.models.agent import AgentStatus


class AgentService:
    def __init__(self, repo: AgentRepository) -> None:
        self._repo = repo

    def _require_agent(self, project_id: uuid.UUID, agent_id: uuid.UUID) -> Agent:
        agent = self._repo.get_agent(agent_id, project_id)
        if not agent:
            raise AppError.not_found("Agent not found", code=ERR_AGENT_NOT_FOUND)
        return agent

    def list_agents(
        self,
        project_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> tuple[list[Agent], int]:
        return self._repo.list_agents(project_id, page=page, page_size=page_size, status=status)

    def get_agent(self, project_id: uuid.UUID, agent_id: uuid.UUID) -> Agent:
        return self._require_agent(project_id, agent_id)

    def create_agent(self, project_id: uuid.UUID, body: AgentCreate) -> Agent:
        return self._repo.create_agent(
            project_id=project_id,
            name=body.name,
            description=body.description,
            system_prompt=body.system_prompt,
            model_config=body.model_config_data,
            status=AgentStatus(body.status),
        )

    def update_agent(self, project_id: uuid.UUID, agent_id: uuid.UUID, body: AgentUpdate) -> Agent:
        agent = self._require_agent(project_id, agent_id)
        updates = body.model_dump(exclude_unset=True, by_alias=True)
        return self._repo.update_agent(agent, **updates)

    def delete_agent(self, project_id: uuid.UUID, agent_id: uuid.UUID) -> None:
        agent = self._require_agent(project_id, agent_id)
        self._repo.delete_agent(agent)

    # ── Tool binding ────────────────────────────────────────────

    def bind_tools(
        self,
        project_id: uuid.UUID,
        agent_id: uuid.UUID,
        items: list[ToolBindItem],
    ) -> list[dict[str, Any]]:
        agent = self._require_agent(project_id, agent_id)

        for item in items:
            if item.type == ToolType.MODEL_INFERENCE and not item.model_id:
                raise AppError.bad_request(
                    f"model_id required for model_inference tool '{item.name}'",
                    code=ERR_AGENT_TOOL_BIND_FAILED,
                )

        self._repo.delete_tools_by_agent(agent_id)

        tools_snapshot: list[dict[str, Any]] = []
        for item in items:
            tool = self._repo.bind_tool(
                agent_id=agent_id,
                name=item.name,
                type=item.type,
                model_id=item.model_id,
                description=item.description,
                config=_build_tool_config(item),
            )
            tools_snapshot.append(_tool_to_snapshot(tool))

        agent = self._repo.update_agent(agent, tools=tools_snapshot)
        return tools_snapshot

    def list_tools(
        self, project_id: uuid.UUID, agent_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        self._require_agent(project_id, agent_id)
        rows = self._repo.list_tools(agent_id)
        return [_tool_to_dict(t) for t in rows]

    # ── Conversation helpers ────────────────────────────────────

    def ensure_conversation(
        self,
        project_id: uuid.UUID,
        agent_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        user_message: str,
    ) -> tuple[Any, uuid.UUID]:
        agent = self._require_agent(project_id, agent_id)
        if agent.status != AgentStatus.ACTIVE:
            raise AppError.bad_request(
                "Agent is not active", code=ERR_AGENT_INVALID_STATUS
            )

        if conversation_id:
            conv = self._repo.get_conversation(conversation_id)
            if not conv or conv.agent_id != agent_id:
                raise AppError.not_found("Conversation not found", code=ERR_AGENT_NOT_FOUND)
        else:
            title = user_message[:50] if len(user_message) > 50 else user_message
            conv = self._repo.create_conversation(agent_id, project_id, title=title)
        return conv, conv.id


def _build_tool_config(item: ToolBindItem) -> dict[str, Any]:
    if item.type == ToolType.MODEL_INFERENCE:
        return {
            "endpoint": f"/api/v1/projects/{{project_id}}/inference/online",
            "model_id": str(item.model_id) if item.model_id else None,
            "params_schema": {
                "type": "object",
                "properties": {"input": {"type": "string", "description": "Model input data"}},
                "required": ["input"],
            },
        }
    return {}


def _tool_to_snapshot(tool: Any) -> dict[str, Any]:
    return {
        "id": str(tool.id),
        "name": tool.name,
        "type": tool.type.value if hasattr(tool.type, "value") else str(tool.type),
        "model_id": str(tool.model_id) if tool.model_id else None,
        "description": tool.description,
    }


def _tool_to_dict(tool: Any) -> dict[str, Any]:
    return {
        "id": str(tool.id),
        "name": tool.name,
        "type": tool.type.value if hasattr(tool.type, "value") else str(tool.type),
        "model_id": str(tool.model_id) if tool.model_id else None,
        "description": tool.description,
        "config": tool.config,
        "created_at": tool.created_at.isoformat() if tool.created_at else None,
    }
