import { http, HttpResponse } from 'msw'
import type { components } from '@/api/types'

import { MOCK_ALT_PROJECT_ID } from '@/mocks/demoIds'

type Agent = components['schemas']['Agent']
type AgentCreate = components['schemas']['AgentCreate']
type AgentTool = components['schemas']['AgentTool']
type AgentUpdate = components['schemas']['AgentUpdate']
type ToolBindRequest = components['schemas']['ToolBindRequest']

const now = '2026-05-19T09:00:00Z'

const mockAgents: Agent[] = [
  {
    id: 'agent-1',
    project_id: MOCK_ALT_PROJECT_ID,
    name: '商品质检助手',
    description: '基于图像分类模型解释批量推理结果',
    system_prompt: '你是一个严谨的商品质检分析助手，会结合模型输出给出可追溯结论。',
    model_config: {
      provider: 'mock',
      model: 'deepflow-mock-agent',
      temperature: 0.4,
      max_tokens: 2048,
    },
    tools: [
      {
        tool_id: 'tool-1',
        name: 'classify_product_image',
        type: 'model_inference',
        description: '调用 ResNet-18 商品分类模型进行图片推理',
        config: {
          model_id: 'model-1',
        },
        bound_at: now,
      },
    ],
    status: 'active',
    created_at: now,
    updated_at: now,
  },
]

function buildResponse(data: unknown, requestId: string) {
  return {
    code: 0,
    message: 'success',
    data,
    request_id: requestId,
  }
}

function findAgent(projectId: string, agentId: string) {
  return mockAgents.find((agent) => agent.project_id === projectId && agent.id === agentId)
}

export const agentHandlers = [
  http.get('/api/v1/projects/:projectId/agents', ({ params }) => {
    const projectId = String(params.projectId)
    const items = mockAgents.filter((agent) => agent.project_id === projectId)

    return HttpResponse.json(
      buildResponse(
        {
          page: 1,
          page_size: 20,
          total: items.length,
          items,
        },
        'mock-p5-agents'
      )
    )
  }),

  http.post('/api/v1/projects/:projectId/agents', async ({ request, params }) => {
    const payload = (await request.json()) as AgentCreate
    const timestamp = new Date().toISOString()
    const agent: Agent = {
      id: `agent-${Date.now()}`,
      project_id: String(params.projectId),
      name: payload.name,
      description: payload.description,
      system_prompt: payload.system_prompt,
      model_config: payload.model_config,
      tools: [],
      status: 'active',
      created_at: timestamp,
      updated_at: timestamp,
    }

    mockAgents.unshift(agent)

    return HttpResponse.json(buildResponse(agent, 'mock-p5-agent-create'), { status: 201 })
  }),

  http.put('/api/v1/projects/:projectId/agents/:agentId', async ({ request, params }) => {
    const projectId = String(params.projectId)
    const agentId = String(params.agentId)
    const payload = (await request.json()) as AgentUpdate
    const agent = findAgent(projectId, agentId)

    if (!agent) {
      return HttpResponse.json(
        {
          code: '70-04-001',
          message: 'agent not found',
          data: null,
          request_id: 'mock-p5-agent-missing',
        },
        { status: 404 }
      )
    }

    Object.assign(agent, payload, { updated_at: new Date().toISOString() })
    return HttpResponse.json(buildResponse(agent, 'mock-p5-agent-update'))
  }),

  http.delete('/api/v1/projects/:projectId/agents/:agentId', ({ params }) => {
    const projectId = String(params.projectId)
    const agentId = String(params.agentId)
    const index = mockAgents.findIndex((agent) => agent.project_id === projectId && agent.id === agentId)

    if (index >= 0) {
      mockAgents.splice(index, 1)
    }

    return HttpResponse.json(buildResponse(null, 'mock-p5-agent-delete'))
  }),

  http.get('/api/v1/projects/:projectId/agents/:agentId/tools', ({ params }) => {
    const agent = findAgent(String(params.projectId), String(params.agentId))
    return HttpResponse.json(buildResponse(agent?.tools ?? [], 'mock-p5-agent-tools'))
  }),

  http.post('/api/v1/projects/:projectId/agents/:agentId/tools/bind', async ({ request, params }) => {
    const agent = findAgent(String(params.projectId), String(params.agentId))
    const payload = (await request.json()) as ToolBindRequest
    const firstTool = payload.tools[0]

    if (!agent || !firstTool) {
      return HttpResponse.json(
        {
          code: '70-04-002',
          message: 'agent or tool not found',
          data: null,
          request_id: 'mock-p5-agent-bind-missing',
        },
        { status: 404 }
      )
    }

    const tool: AgentTool = {
      tool_id: `tool-${Date.now()}`,
      name: firstTool.name,
      type: firstTool.type,
      description: firstTool.description,
      config: {
        ...firstTool.config,
        model_id: firstTool.model_id,
      },
      bound_at: new Date().toISOString(),
    }

    agent.tools = [...(agent.tools ?? []), tool]
    agent.updated_at = new Date().toISOString()

    return HttpResponse.json(buildResponse(tool, 'mock-p5-agent-tool-bind'))
  }),
]
