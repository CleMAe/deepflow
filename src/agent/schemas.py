"""Pydantic request/response schemas for Agent API."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from shared.protocols import ToolType


# ── Request models ─────────────────────────────────────────────


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: str | None = None
    system_prompt: str | None = None
    model_config_data: dict[str, Any] | None = Field(None, alias="model_config")
    status: str = "active"


class AgentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=256)
    description: str | None = None
    system_prompt: str | None = None
    model_config_data: dict[str, Any] | None = Field(None, alias="model_config")
    status: str | None = None


class ToolBindItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    type: ToolType = ToolType.MODEL_INFERENCE
    model_id: UUID | None = None
    description: str | None = None


class ToolBindRequest(BaseModel):
    tools: list[ToolBindItem]


class ChatRequest(BaseModel):
    message: str
    conversation_id: UUID | None = None


class PromptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    template: str
    description: str | None = None


class PromptRenderRequest(BaseModel):
    variables: dict[str, str] = Field(default_factory=dict)


# ── Response models ────────────────────────────────────────────


class ToolOut(BaseModel):
    id: UUID
    name: str
    type: ToolType
    model_id: UUID | None = None
    description: str | None = None
    config: dict[str, Any] | None = None
    created_at: datetime | None = None


class AgentOut(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str | None = None
    system_prompt: str | None = None
    llm_config: dict[str, Any] | None = Field(None, alias="model_config")
    tools: list[dict[str, Any]] | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class AgentListOut(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[AgentOut]


class ChatHistoryMessage(BaseModel):
    id: UUID
    role: str
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    created_at: datetime | None = None


class ChatHistoryOut(BaseModel):
    conversation_id: UUID
    messages: list[ChatHistoryMessage]
    total: int


class PromptOut(BaseModel):
    id: UUID
    agent_id: UUID
    name: str
    template: str
    description: str | None = None
    variables: list[str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
