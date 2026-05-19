import api, { type ApiResponse } from '@/lib/axios'
import type { components } from '@/api/types'

export type Agent = components['schemas']['Agent']
export type AgentCreate = components['schemas']['AgentCreate']
export type AgentTool = components['schemas']['AgentTool']
export type AgentUpdate = components['schemas']['AgentUpdate']
export type PaginatedAgents = components['schemas']['PaginatedAgents']
export type ToolBindRequest = components['schemas']['ToolBindRequest']

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
