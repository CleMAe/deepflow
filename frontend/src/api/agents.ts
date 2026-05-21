import api, { type ApiResponse } from '@/lib/axios'
import type { components } from '@/api/types'

export type Agent = components['schemas']['Agent']
export type AgentCreate = components['schemas']['AgentCreate']
export type AgentTool = components['schemas']['AgentTool']
export type AgentUpdate = components['schemas']['AgentUpdate']
export type ChatMessage = components['schemas']['ChatMessage']
export type ChatRequest = components['schemas']['ChatRequest']
export type PaginatedChatHistory = components['schemas']['PaginatedChatHistory']
export type AgentChatHistory = PaginatedChatHistory & {
  conversation_id?: string
  messages?: ChatMessage[]
}
export type PaginatedAgents = components['schemas']['PaginatedAgents']
export type PromptTemplate = components['schemas']['PromptTemplate']
export type PromptTemplateCreate = components['schemas']['PromptTemplateCreate']
export type ToolBindRequest = components['schemas']['ToolBindRequest']

export interface ChatHistoryQuery {
  conversationId?: string
  page?: number
  pageSize?: number
}

export interface AgentStreamEvent {
  type: 'token' | 'content' | 'tool_call' | 'tool_result' | 'done' | 'error'
  content?: string
  text?: string
  name?: string
  tool?: string
  args?: Record<string, unknown>
  result?: unknown
  message_id?: string
  conversation_id?: string
}

function unwrapApiData<T>(res: unknown) {
  return (res as ApiResponse<T>).data
}

export async function listAgents(projectId: string) {
  const res = await api.get(`/projects/${projectId}/agents`)
  return unwrapApiData<PaginatedAgents>(res)
}

export async function createAgent(projectId: string, payload: AgentCreate) {
  const res = await api.post(`/projects/${projectId}/agents`, payload)
  return unwrapApiData<Agent>(res)
}

export async function updateAgent(projectId: string, agentId: string, payload: AgentUpdate) {
  const res = await api.put(`/projects/${projectId}/agents/${agentId}`, payload)
  return unwrapApiData<Agent>(res)
}

export async function deleteAgent(projectId: string, agentId: string) {
  await api.delete(`/projects/${projectId}/agents/${agentId}`)
}

export async function bindAgentTools(projectId: string, agentId: string, payload: ToolBindRequest) {
  const res = await api.post(`/projects/${projectId}/agents/${agentId}/tools/bind`, payload)
  return unwrapApiData<AgentTool>(res)
}

export async function listAgentTools(projectId: string, agentId: string) {
  const res = await api.get(`/projects/${projectId}/agents/${agentId}/tools`)
  return unwrapApiData<AgentTool[]>(res)
}

export async function listPromptTemplates(projectId: string, agentId: string) {
  const res = await api.get(`/projects/${projectId}/agents/${agentId}/prompts`)
  return unwrapApiData<PromptTemplate[]>(res)
}

export async function savePromptTemplate(
  projectId: string,
  agentId: string,
  payload: PromptTemplateCreate
) {
  const res = await api.post(`/projects/${projectId}/agents/${agentId}/prompts`, payload)
  return unwrapApiData<PromptTemplate>(res)
}

export async function getChatHistory(
  projectId: string,
  agentId: string,
  query: ChatHistoryQuery = {}
) {
  const { conversationId, page = 1, pageSize = 50 } = query
  const res = await api.get(`/projects/${projectId}/agents/${agentId}/chat/history`, {
    params: {
      ...(conversationId ? { conversation_id: conversationId } : {}),
      page,
      page_size: pageSize,
    },
  })
  return unwrapApiData<AgentChatHistory>(res)
}

export async function streamAgentChat(
  projectId: string,
  agentId: string,
  payload: ChatRequest,
  handlers: {
    onEvent: (event: AgentStreamEvent) => void
    signal?: AbortSignal
  }
) {
  const token = localStorage.getItem('access_token')
  const response = await fetch(`/api/v1/projects/${projectId}/agents/${agentId}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
    signal: handlers.signal,
  })

  if (!response.ok) {
    throw new Error(`Agent chat failed: ${response.status}`)
  }

  if (!response.body) {
    throw new Error('Agent chat stream is empty')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const emitChunk = (chunk: string) => {
    const lines = chunk.split(/\r?\n/)
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith(':')) {
        continue
      }

      const payloadText = trimmed.startsWith('data:') ? trimmed.slice(5).trim() : trimmed
      if (!payloadText || payloadText === '[DONE]') {
        continue
      }

      try {
        handlers.onEvent(JSON.parse(payloadText) as AgentStreamEvent)
      } catch {
        handlers.onEvent({ type: 'token', content: payloadText })
      }
    }
  }

  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const chunks = buffer.split(/\n\n|\r\n\r\n/)
    buffer = chunks.pop() ?? ''

    for (const chunk of chunks) {
      emitChunk(chunk)
    }

    if (done) {
      break
    }
  }

  if (buffer.trim()) {
    emitChunk(buffer)
  }
}
