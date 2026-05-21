"""Agent API routes — 12 endpoints (CRUD + tool binding + chat + prompts)."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_inference_service, require_project_access
from app.core.response import success
from app.db.session import get_db
from app.services.inference_service import InferenceService
from src.agent.chat_engine import ChatEngine
from src.agent.prompt_manager import PromptManager
from src.agent.repository import AgentRepository
from src.agent.schemas import (
    AgentCreate,
    AgentListOut,
    AgentOut,
    AgentUpdate,
    ChatHistoryMessage,
    ChatHistoryOut,
    ChatRequest,
    PromptCreate,
    PromptRenderRequest,
    ToolBindRequest,
)
from src.agent.service import AgentService
from src.agent.tool_wrapper import ToolWrapper

router = APIRouter(prefix="/projects/{project_id}/agents", tags=["Agent"])


def _agent_to_out(a: object) -> AgentOut:
    return AgentOut(
        id=a.id,
        project_id=a.project_id,
        name=a.name,
        description=a.description,
        system_prompt=a.system_prompt,
        llm_config=a.model_config,
        tools=a.tools,
        status=a.status.value if hasattr(a.status, "value") else str(a.status),
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


def _get_deps(
    db: Session = Depends(get_db),
    _pid: UUID = Depends(require_project_access),
    inference_svc: InferenceService = Depends(get_inference_service),
):
    repo = AgentRepository(db)
    service = AgentService(repo)
    tool_wrapper = ToolWrapper(repo, inference_service=inference_svc, db=db)
    chat_engine = ChatEngine(repo, tool_wrapper)
    prompt_manager = PromptManager(repo)
    return repo, service, chat_engine, prompt_manager, db


# ── CRUD ────────────────────────────────────────────────────────


@router.get("")
async def list_agents(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    deps: tuple = Depends(_get_deps),
):
    _, service, _, _, _ = deps
    rows, total = service.list_agents(project_id, page=page, page_size=page_size, status=status)
    items = [_agent_to_out(a) for a in rows]
    return success(AgentListOut(page=page, page_size=page_size, total=total, items=items).model_dump(mode="json"))


@router.post("", status_code=201)
async def create_agent(
    project_id: UUID,
    body: AgentCreate,
    deps: tuple = Depends(_get_deps),
):
    _, service, _, _, db = deps
    agent = service.create_agent(project_id, body)
    db.commit()
    return success(_agent_to_out(agent).model_dump(mode="json"))


@router.get("/{agent_id}")
async def get_agent(
    project_id: UUID,
    agent_id: UUID,
    deps: tuple = Depends(_get_deps),
):
    _, service, _, _, _ = deps
    agent = service.get_agent(project_id, agent_id)
    return success(_agent_to_out(agent).model_dump(mode="json"))


@router.put("/{agent_id}")
async def update_agent(
    project_id: UUID,
    agent_id: UUID,
    body: AgentUpdate,
    deps: tuple = Depends(_get_deps),
):
    _, service, _, _, db = deps
    agent = service.update_agent(project_id, agent_id, body)
    db.commit()
    return success(_agent_to_out(agent).model_dump(mode="json"))


@router.delete("/{agent_id}")
async def delete_agent(
    project_id: UUID,
    agent_id: UUID,
    deps: tuple = Depends(_get_deps),
):
    _, service, _, _, db = deps
    service.delete_agent(project_id, agent_id)
    db.commit()
    return success(None)


# ── Tool binding ────────────────────────────────────────────────


@router.post("/{agent_id}/tools/bind")
async def bind_tools(
    project_id: UUID,
    agent_id: UUID,
    body: ToolBindRequest,
    deps: tuple = Depends(_get_deps),
):
    _, service, _, _, db = deps
    result = service.bind_tools(project_id, agent_id, body.tools)
    db.commit()
    return success(result)


@router.get("/{agent_id}/tools")
async def list_tools(
    project_id: UUID,
    agent_id: UUID,
    deps: tuple = Depends(_get_deps),
):
    _, service, _, _, _ = deps
    return success(service.list_tools(project_id, agent_id))


# ── Chat (SSE) ──────────────────────────────────────────────────


@router.post("/{agent_id}/chat")
async def agent_chat(
    project_id: UUID,
    agent_id: UUID,
    body: ChatRequest,
    deps: tuple = Depends(_get_deps),
):
    from sse_starlette.sse import EventSourceResponse

    repo, service, chat_engine, _, db = deps
    agent = service.get_agent(project_id, agent_id)
    conv, conv_id = service.ensure_conversation(
        project_id, agent_id, body.conversation_id, body.message
    )
    db.commit()

    async def event_generator():
        async for event in chat_engine.chat(
            agent_id=agent_id,
            conversation_id=conv_id,
            user_message=body.message,
            system_prompt=agent.system_prompt,
            model_config=agent.model_config,
        ):
            yield json.dumps(
                {"type": event.type.value, "content": event.content, "name": event.name,
                 "args": event.args, "result": event.result, "message_id": event.message_id},
                ensure_ascii=False,
            )

    return EventSourceResponse(event_generator())


@router.get("/{agent_id}/chat/history")
async def chat_history(
    project_id: UUID,
    agent_id: UUID,
    conversation_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    deps: tuple = Depends(_get_deps),
):
    repo, service, _, _, _ = deps
    service.get_agent(project_id, agent_id)  # verify agent exists
    conv = repo.get_conversation(conversation_id)
    if not conv or conv.agent_id != agent_id:
        from app.core.errors import ERR_AGENT_NOT_FOUND, AppError
        raise AppError.not_found("Conversation not found", code=ERR_AGENT_NOT_FOUND)

    total = repo.count_messages(conversation_id)
    messages = repo.get_messages(conversation_id, limit=page_size)
    msg_outs = [
        ChatHistoryMessage(
            id=m.id,
            role=m.role.value,
            content=m.content,
            tool_calls=m.tool_calls,
            tool_call_id=m.tool_call_id,
            created_at=m.created_at,
        )
        for m in messages
    ]
    return success(
        ChatHistoryOut(conversation_id=conversation_id, messages=msg_outs, total=total).model_dump(mode="json")
    )


# ── Prompt templates ────────────────────────────────────────────


@router.post("/{agent_id}/prompts", status_code=201)
async def create_prompt(
    project_id: UUID,
    agent_id: UUID,
    body: PromptCreate,
    deps: tuple = Depends(_get_deps),
):
    _, service, _, prompt_manager, db = deps
    service.get_agent(project_id, agent_id)  # verify agent exists
    result = prompt_manager.create_prompt(agent_id, body)
    db.commit()
    return success(result)


@router.get("/{agent_id}/prompts")
async def list_prompts(
    project_id: UUID,
    agent_id: UUID,
    deps: tuple = Depends(_get_deps),
):
    _, service, _, prompt_manager, _ = deps
    service.get_agent(project_id, agent_id)  # verify agent exists
    return success(prompt_manager.list_prompts(agent_id))


@router.post("/{agent_id}/prompts/{prompt_id}/render")
async def render_prompt(
    project_id: UUID,
    agent_id: UUID,
    prompt_id: UUID,
    body: PromptRenderRequest,
    deps: tuple = Depends(_get_deps),
):
    _, service, _, prompt_manager, _ = deps
    service.get_agent(project_id, agent_id)  # verify agent exists
    rendered = prompt_manager.render_prompt(agent_id, prompt_id, body.variables)
    return success({"rendered": rendered})
