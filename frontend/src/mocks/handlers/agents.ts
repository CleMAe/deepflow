import { http, HttpResponse } from 'msw'
import type { components } from '@/api/types'

import { MOCK_ALT_PROJECT_ID } from '@/mocks/demoIds'

type Agent = components['schemas']['Agent']
type AgentCreate = components['schemas']['AgentCreate']
type AgentTool = components['schemas']['AgentTool']
type AgentUpdate = components['schemas']['AgentUpdate']
type ChatRequest = components['schemas']['ChatRequest']
type ChatMessage = components['schemas']['ChatMessage']
type PromptTemplate = components['schemas']['PromptTemplate']
type PromptTemplateCreate = components['schemas']['PromptTemplateCreate']
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

const mockPromptTemplates: PromptTemplate[] = [
  {
    id: 'prompt-1',
    agent_id: 'agent-1',
    name: '质检分析模板',
    template: '请结合模型推理结果、置信度和异常类别，为业务同学生成一段可执行的质检建议。',
    description: '用于商品图像分类后的结果解释',
    variables: ['prediction', 'confidence'],
    created_at: now,
    updated_at: now,
  },
]

const mockChatMessages: ChatMessage[] = [
  {
    id: 'message-1',
    conversation_id: 'conversation-mock-1',
    role: 'user',
    content: '请分析最近一次批量推理结果。',
    created_at: '2026-05-19T09:02:00Z',
  },
  {
    id: 'message-2',
    conversation_id: 'conversation-mock-1',
    role: 'assistant',
    content:
      '已调用模型推理工具，发现 item_0002.jpg 为轻微异常，建议优先复核图片清晰度和标签一致性。',
    tool_calls: [
      {
        name: 'model_predict',
        arguments: { sample: 'item_0002.jpg' },
        result: { prediction: '轻微异常', confidence: 0.873 },
      },
    ],
    created_at: '2026-05-19T09:02:08Z',
  },
  {
    id: 'message-3',
    conversation_id: 'conversation-mock-1',
    role: 'user',
    content: '这个异常是否需要重新训练模型？',
    created_at: '2026-05-19T09:05:00Z',
  },
  {
    id: 'message-4',
    conversation_id: 'conversation-mock-1',
    role: 'assistant',
    content: '暂不建议直接重训。当前更像输入质量问题，先补充人工复核标签，再观察下一批次异常分布。',
    created_at: '2026-05-19T09:05:06Z',
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
    const index = mockAgents.findIndex(
      (agent) => agent.project_id === projectId && agent.id === agentId
    )

    if (index >= 0) {
      mockAgents.splice(index, 1)
    }

    return HttpResponse.json(buildResponse(null, 'mock-p5-agent-delete'))
  }),

  http.get('/api/v1/projects/:projectId/agents/:agentId/tools', ({ params }) => {
    const agent = findAgent(String(params.projectId), String(params.agentId))
    return HttpResponse.json(buildResponse(agent?.tools ?? [], 'mock-p5-agent-tools'))
  }),

  http.post(
    '/api/v1/projects/:projectId/agents/:agentId/tools/bind',
    async ({ request, params }) => {
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
    }
  ),

  http.post('/api/v1/projects/:projectId/agents/:agentId/chat', async ({ request, params }) => {
    const payload = (await request.json()) as ChatRequest
    const encoder = new TextEncoder()
    const agent = findAgent(String(params.projectId), String(params.agentId))
    const toolName = agent?.tools?.[0]?.name ?? 'model_predict'
    const conversationId = payload.conversation_id ?? 'conversation-mock-1'
    const timestamp = new Date().toISOString()
    const events = [
      { type: 'token', content: '已收到你的问题。' },
      { type: 'tool_call', name: toolName, args: { input: payload.message, top_k: 3 } },
      {
        type: 'tool_result',
        name: toolName,
        result: {
          prediction: '轻微异常',
          confidence: 0.873,
          latency_ms: 42,
        },
      },
      { type: 'token', content: '模型工具返回轻微异常，置信度 87.3%。' },
      { type: 'token', content: '建议优先复核图片清晰度、商品边缘遮挡和标签一致性。' },
      { type: 'done', message_id: `msg-${Date.now()}`, conversation_id: conversationId },
    ]

    mockChatMessages.push(
      {
        id: `message-${Date.now()}-user`,
        conversation_id: conversationId,
        role: 'user',
        content: payload.message,
        created_at: timestamp,
      },
      {
        id: `message-${Date.now()}-assistant`,
        conversation_id: conversationId,
        role: 'assistant',
        content:
          '模型工具返回轻微异常，置信度 87.3%。建议优先复核图片清晰度、商品边缘遮挡和标签一致性。',
        tool_calls: [
          {
            name: toolName,
            arguments: { input: payload.message, top_k: 3 },
            result: { prediction: '轻微异常', confidence: 0.873, latency_ms: 42 },
          },
        ],
        created_at: timestamp,
      }
    )

    const stream = new ReadableStream({
      async start(controller) {
        for (const event of events) {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`))
          await new Promise((resolve) => window.setTimeout(resolve, 120))
        }
        controller.close()
      },
    })

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
    })
  }),

  http.get('/api/v1/projects/:projectId/agents/:agentId/chat/history', ({ request }) => {
    const url = new URL(request.url)
    const conversationId = url.searchParams.get('conversation_id') ?? 'conversation-mock-1'
    const page = Number(url.searchParams.get('page') ?? 1)
    const pageSize = Number(url.searchParams.get('page_size') ?? 50)
    const items = mockChatMessages.filter((message) => message.conversation_id === conversationId)
    const start = (page - 1) * pageSize
    const pagedItems = items.slice(start, start + pageSize)

    return HttpResponse.json(
      buildResponse(
        {
          conversation_id: conversationId,
          messages: pagedItems,
          page,
          page_size: pageSize,
          total: items.length,
          items: pagedItems,
        },
        'mock-p5-agent-history'
      )
    )
  }),

  http.get('/api/v1/projects/:projectId/agents/:agentId/prompts', ({ params }) => {
    const items = mockPromptTemplates.filter((template) => template.agent_id === params.agentId)
    return HttpResponse.json(buildResponse(items, 'mock-p5-agent-prompts'))
  }),

  http.post('/api/v1/projects/:projectId/agents/:agentId/prompts', async ({ request, params }) => {
    const payload = (await request.json()) as PromptTemplateCreate
    const timestamp = new Date().toISOString()
    const template: PromptTemplate = {
      id: `prompt-${Date.now()}`,
      agent_id: String(params.agentId),
      name: payload.name,
      template: payload.template,
      description: payload.description,
      variables: payload.variables,
      created_at: timestamp,
      updated_at: timestamp,
    }

    mockPromptTemplates.unshift(template)

    return HttpResponse.json(buildResponse(template, 'mock-p5-agent-prompt-save'), { status: 201 })
  }),
]
