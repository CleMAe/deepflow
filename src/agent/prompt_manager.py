"""Prompt template CRUD + $variable rendering."""

from __future__ import annotations

import uuid
from string import Template
from typing import Any

from app.core.errors import AppError, ERR_AGENT_NOT_FOUND, ERR_AGENT_PROMPT_RENDER_FAILED
from src.agent.repository import AgentRepository
from src.agent.schemas import PromptCreate


class PromptManager:
    def __init__(self, repo: AgentRepository) -> None:
        self._repo = repo

    def list_prompts(self, agent_id: uuid.UUID) -> list[dict[str, Any]]:
        rows = self._repo.list_prompts(agent_id)
        return [_prompt_to_dict(p) for p in rows]

    def create_prompt(
        self, agent_id: uuid.UUID, body: PromptCreate
    ) -> dict[str, Any]:
        pt = self._repo.create_prompt(
            agent_id=agent_id,
            name=body.name,
            template=body.template,
            description=body.description,
        )
        return _prompt_to_dict(pt)

    def render_prompt(
        self,
        agent_id: uuid.UUID,
        prompt_id: uuid.UUID,
        variables: dict[str, str],
    ) -> str:
        pt = self._repo.get_prompt(prompt_id)
        if not pt or pt.agent_id != agent_id:
            raise AppError.not_found("Prompt template not found", code=ERR_AGENT_NOT_FOUND)
        try:
            return Template(pt.template).safe_substitute(variables)
        except (KeyError, ValueError) as exc:
            raise AppError.bad_request(
                f"Prompt render failed: {exc}",
                code=ERR_AGENT_PROMPT_RENDER_FAILED,
            )


def _prompt_to_dict(pt: Any) -> dict[str, Any]:
    return {
        "id": str(pt.id),
        "agent_id": str(pt.agent_id),
        "name": pt.name,
        "template": pt.template,
        "description": pt.description,
        "variables": pt.variables,
        "created_at": pt.created_at.isoformat() if pt.created_at else None,
        "updated_at": pt.updated_at.isoformat() if pt.updated_at else None,
    }
