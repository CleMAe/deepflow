"""DB query layer for Agent, AgentTool, Conversation, ChatMessage, PromptTemplate."""

from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.protocols import ChatRole
from src.infra.db.models import Agent, AgentTool, ChatMessage, Conversation, PromptTemplate
from src.infra.db.models.agent import AgentStatus


class AgentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    # ── Agent CRUD ──────────────────────────────────────────────

    def list_agents(
        self,
        project_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> tuple[list[Agent], int]:
        q = select(Agent).where(Agent.project_id == project_id)
        if status:
            q = q.where(Agent.status == AgentStatus(status))
        total = self._db.scalar(select(func.count()).select_from(q.subquery()))
        rows = (
            self._db.scalars(
                q.order_by(Agent.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .all()
        )
        return list(rows), total or 0

    def get_agent(self, agent_id: uuid.UUID, project_id: uuid.UUID) -> Agent | None:
        return self._db.scalar(
            select(Agent).where(Agent.id == agent_id, Agent.project_id == project_id)
        )

    def create_agent(self, **kwargs: Any) -> Agent:
        agent = Agent(**kwargs)
        self._db.add(agent)
        self._db.flush()
        return agent

    def update_agent(self, agent: Agent, **kwargs: Any) -> Agent:
        for k, v in kwargs.items():
            if v is not None:
                if k == "model_config_data":
                    k = "model_config"
                if k == "status":
                    v = AgentStatus(v)
                setattr(agent, k, v)
        self._db.flush()
        return agent

    def delete_agent(self, agent: Agent) -> None:
        self._db.delete(agent)
        self._db.flush()

    # ── AgentTool ───────────────────────────────────────────────

    def list_tools(self, agent_id: uuid.UUID) -> list[AgentTool]:
        rows = self._db.scalars(
            select(AgentTool).where(AgentTool.agent_id == agent_id).order_by(AgentTool.created_at)
        ).all()
        return list(rows)

    def bind_tool(self, agent_id: uuid.UUID, **kwargs: Any) -> AgentTool:
        tool = AgentTool(agent_id=agent_id, **kwargs)
        self._db.add(tool)
        self._db.flush()
        return tool

    def get_tool(self, tool_id: uuid.UUID) -> AgentTool | None:
        return self._db.get(AgentTool, tool_id)

    def delete_tools_by_agent(self, agent_id: uuid.UUID) -> None:
        for t in self.list_tools(agent_id):
            self._db.delete(t)
        self._db.flush()

    # ── Conversation ────────────────────────────────────────────

    def create_conversation(
        self, agent_id: uuid.UUID, project_id: uuid.UUID, title: str | None = None
    ) -> Conversation:
        conv = Conversation(agent_id=agent_id, project_id=project_id, title=title)
        self._db.add(conv)
        self._db.flush()
        return conv

    def get_conversation(self, conversation_id: uuid.UUID) -> Conversation | None:
        return self._db.get(Conversation, conversation_id)

    # ── ChatMessage ─────────────────────────────────────────────

    def add_message(
        self,
        conversation_id: uuid.UUID,
        role: ChatRole,
        content: str,
        tool_calls: list[dict] | None = None,
        tool_call_id: str | None = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
        )
        self._db.add(msg)
        self._db.flush()
        return msg

    def get_messages(
        self,
        conversation_id: uuid.UUID,
        limit: int = 50,
    ) -> list[ChatMessage]:
        rows = self._db.scalars(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        ).all()
        return list(reversed(rows))

    def count_messages(self, conversation_id: uuid.UUID) -> int:
        return self._db.scalar(
            select(func.count())
            .select_from(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
        ) or 0

    # ── PromptTemplate ──────────────────────────────────────────

    def list_prompts(self, agent_id: uuid.UUID) -> list[PromptTemplate]:
        return list(
            self._db.scalars(
                select(PromptTemplate)
                .where(PromptTemplate.agent_id == agent_id)
                .order_by(PromptTemplate.created_at.desc())
            ).all()
        )

    def create_prompt(self, agent_id: uuid.UUID, **kwargs: Any) -> PromptTemplate:
        template_str = kwargs.get("template", "")
        kwargs.setdefault("variables", _extract_variables(template_str))
        pt = PromptTemplate(agent_id=agent_id, **kwargs)
        self._db.add(pt)
        self._db.flush()
        return pt

    def get_prompt(self, prompt_id: uuid.UUID) -> PromptTemplate | None:
        return self._db.get(PromptTemplate, prompt_id)

    def commit(self) -> None:
        self._db.commit()


def _extract_variables(template: str) -> list[str]:
    return sorted(set(re.findall(r"\$(\w+)", template)))
