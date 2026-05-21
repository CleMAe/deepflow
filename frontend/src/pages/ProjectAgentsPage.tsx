import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Empty,
  Form,
  Input,
  InputNumber,
  List,
  Modal,
  Popconfirm,
  Row,
  Select,
  Statistic,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  DeleteOutlined,
  LinkOutlined,
  PlusOutlined,
  ReloadOutlined,
  SendOutlined,
  StopOutlined,
} from '@ant-design/icons'
import {
  bindAgentTools,
  createAgent,
  deleteAgent,
  getChatHistory,
  listAgentTools,
  listAgents,
  listPromptTemplates,
  savePromptTemplate,
  streamAgentChat,
  type Agent,
  type AgentCreate,
  type AgentStreamEvent,
  type AgentTool,
  type ChatMessage,
  type PromptTemplate,
  type PromptTemplateCreate,
} from '@/api/agents'
import { listInferenceModels, type Model } from '@/api/inference'

const { Paragraph, Text } = Typography
const MAX_TOOL_EVENTS = 40
const DEFAULT_CONVERSATION_ID = 'conversation-mock-1'

type AgentModelConfig = NonNullable<AgentCreate['model_config']>
type AgentProvider = AgentModelConfig['provider']
type ChatRole = 'user' | 'assistant'
type HistoryRole = NonNullable<ChatMessage['role']>
type ToolTimelineItem = {
  id: string
  type: 'tool_call' | 'tool_result' | 'error'
  name?: string
  detail?: unknown
}
type LocalChatMessage = {
  id: string
  role: ChatRole
  content: string
}

interface CreateAgentFormValues {
  name: string
  description?: string
  system_prompt?: string
  provider: AgentProvider
  model: string
  temperature: number
  max_tokens: number
}

interface BindToolFormValues {
  name: string
  model_id: string
  description?: string
}

interface PromptFormValues {
  name: string
  description?: string
  template: string
  variables?: string
}

interface PromptPreviewValues {
  prediction: string
  confidence: string
  context: string
}

function formatDate(value?: string) {
  if (!value) {
    return '-'
  }
  return new Date(value).toLocaleString()
}

function stringifyValue(value: unknown) {
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  return JSON.stringify(value)
}

function parseVariables(value?: string) {
  return (
    value
      ?.split(',')
      .map((item) => item.trim())
      .filter(Boolean) ?? []
  )
}

function extractTemplateVariables(template?: string) {
  return Array.from(
    new Set(template?.match(/\$[A-Za-z_][\w-]*/g)?.map((item) => item.slice(1)) ?? [])
  )
}

function renderPromptPreview(template: string, variables: Record<string, string>) {
  return template.replace(
    /\$([A-Za-z_][\w-]*)/g,
    (_match, name: string) => variables[name] ?? `$${name}`
  )
}

function getChatConversationId(value?: string) {
  const trimmed = value?.trim()
  if (!trimmed) {
    return undefined
  }

  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(trimmed)
    ? trimmed
    : undefined
}

function modelLabel(model: Model) {
  return `${model.name ?? model.id} · ${model.arch_type ?? 'custom'}`
}

function agentStatusColor(status?: Agent['status']) {
  return status === 'active' ? 'green' : 'default'
}

function agentStatusLabel(status?: Agent['status']) {
  return status === 'active' ? '启用' : '停用'
}

function getAgentModelName(agent?: Agent) {
  const config = agent?.model_config ?? {}
  return String(config.model ?? 'mock')
}

function getAgentProviderName(agent?: Agent) {
  const config = agent?.model_config ?? {}
  return String(config.provider ?? 'mock')
}

function getAgentConfigValue(agent: Agent | undefined, key: string) {
  const value = agent?.model_config?.[key]
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  return '-'
}

function getEventText(event: AgentStreamEvent) {
  return event.content ?? event.text ?? ''
}

function roleLabel(role?: HistoryRole) {
  const labels: Record<HistoryRole, string> = {
    user: '用户',
    assistant: 'Agent',
    system: '系统',
    tool: '工具',
  }
  return role ? labels[role] : '消息'
}

function roleColor(role?: HistoryRole) {
  const colors: Record<HistoryRole, string> = {
    user: 'blue',
    assistant: 'green',
    system: 'purple',
    tool: 'orange',
  }
  return role ? colors[role] : 'default'
}

function appendLatestAssistantMessage(messages: LocalChatMessage[], text: string) {
  return messages.map((item, index) =>
    index === messages.length - 1 && item.role === 'assistant'
      ? { ...item, content: `${item.content}${text}` }
      : item
  )
}

function renderToolTags(tools?: AgentTool[]) {
  if (!tools?.length) {
    return <Text type="secondary">未绑定</Text>
  }

  return (
    <Space size={[0, 8]} wrap>
      {tools.map((tool) => (
        <Tag
          key={tool.tool_id ?? tool.name}
          color={tool.type === 'model_inference' ? 'blue' : 'default'}
        >
          {tool.name}
        </Tag>
      ))}
    </Space>
  )
}

function renderCompactToolTags(tools?: AgentTool[]) {
  if (!tools?.length) {
    return <Text type="secondary">未绑定工具</Text>
  }

  const visibleTools = tools.slice(0, 3)
  const hiddenCount = tools.length - visibleTools.length

  return (
    <Space size={[4, 6]} wrap>
      {visibleTools.map((tool) => (
        <Tag
          key={tool.tool_id ?? tool.name}
          color={tool.type === 'model_inference' ? 'blue' : 'default'}
          style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis' }}
        >
          {tool.name}
        </Tag>
      ))}
      {hiddenCount > 0 && <Tag>+{hiddenCount}</Tag>}
    </Space>
  )
}

function ToolTimeline({ items }: { items: ToolTimelineItem[] }) {
  if (!items.length) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无工具事件" />
  }

  return (
    <List
      size="small"
      dataSource={items}
      renderItem={(item) => (
        <List.Item>
          <Space direction="vertical" size={4} style={{ width: '100%' }}>
            <Space>
              <Tag
                color={
                  item.type === 'tool_call' ? 'blue' : item.type === 'tool_result' ? 'green' : 'red'
                }
              >
                {item.type === 'tool_call'
                  ? '工具调用'
                  : item.type === 'tool_result'
                    ? '工具结果'
                    : '错误'}
              </Tag>
              <Text strong>{item.name ?? 'agent'}</Text>
            </Space>
            <Text code style={{ whiteSpace: 'normal' }}>
              {stringifyValue(item.detail)}
            </Text>
          </Space>
        </List.Item>
      )}
    />
  )
}

function ChatMessages({ messages }: { messages: LocalChatMessage[] }) {
  if (!messages.length) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无对话消息" />
  }

  return (
    <Space direction="vertical" size={12} style={{ width: '100%' }}>
      {messages.map((item) => (
        <div
          key={item.id}
          style={{
            display: 'flex',
            justifyContent: item.role === 'user' ? 'flex-end' : 'flex-start',
          }}
        >
          <div
            style={{
              maxWidth: '78%',
              padding: '10px 12px',
              borderRadius: 8,
              background: item.role === 'user' ? '#e6f4ff' : '#f6ffed',
              border: `1px solid ${item.role === 'user' ? '#91caff' : '#b7eb8f'}`,
              whiteSpace: 'pre-wrap',
            }}
          >
            <Text strong>{item.role === 'user' ? '用户' : 'Agent'}</Text>
            <div style={{ marginTop: 6 }}>{item.content || '...'}</div>
          </div>
        </div>
      ))}
    </Space>
  )
}

function HistoryMessages({ messages }: { messages: ChatMessage[] }) {
  if (!messages.length) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无对话日志" />
  }

  return (
    <List
      dataSource={messages}
      renderItem={(item) => (
        <List.Item>
          <Space direction="vertical" size={8} style={{ width: '100%' }}>
            <Space
              style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}
              align="start"
            >
              <Space size={8} wrap>
                <Tag color={roleColor(item.role)}>{roleLabel(item.role)}</Tag>
                <Text type="secondary">{formatDate(item.created_at)}</Text>
              </Space>
              {item.conversation_id && <Text type="secondary">会话 {item.conversation_id}</Text>}
            </Space>
            <Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
              {item.content || '-'}
            </Paragraph>
            {!!item.tool_calls?.length && (
              <Space direction="vertical" size={6} style={{ width: '100%' }}>
                {item.tool_calls.map((toolCall, index) => (
                  <div
                    key={`${toolCall.name ?? 'tool'}-${index}`}
                    style={{
                      border: '1px solid #d9d9d9',
                      borderRadius: 8,
                      padding: 10,
                      background: '#fafafa',
                    }}
                  >
                    <Space direction="vertical" size={4} style={{ width: '100%' }}>
                      <Space>
                        <Tag color="orange">工具调用</Tag>
                        <Text strong>{toolCall.name ?? 'tool'}</Text>
                      </Space>
                      <Text code style={{ whiteSpace: 'normal' }}>
                        参数：{stringifyValue(toolCall.arguments ?? {})}
                      </Text>
                      <Text code style={{ whiteSpace: 'normal' }}>
                        结果：{stringifyValue(toolCall.result ?? {})}
                      </Text>
                    </Space>
                  </div>
                ))}
              </Space>
            )}
          </Space>
        </List.Item>
      )}
    />
  )
}

export default function ProjectAgentsPage() {
  const { projectId } = useParams()
  const queryClient = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  const [createOpen, setCreateOpen] = useState(false)
  const [bindOpen, setBindOpen] = useState(false)
  const [selectedAgentId, setSelectedAgentId] = useState<string>()
  const [selectedToolAgent, setSelectedToolAgent] = useState<Agent>()
  const [chatInput, setChatInput] = useState(
    '请结合已绑定模型工具，分析最近一次批量推理中的异常样本。'
  )
  const [conversationId, setConversationId] = useState(DEFAULT_CONVERSATION_ID)
  const [chatMessages, setChatMessages] = useState<LocalChatMessage[]>([])
  const [toolEvents, setToolEvents] = useState<ToolTimelineItem[]>([])
  const [streaming, setStreaming] = useState(false)
  const streamAbortRef = useRef<AbortController>()
  const chatScrollRef = useRef<HTMLDivElement>(null)
  const tokenBufferRef = useRef('')
  const flushTimerRef = useRef<number>()
  const [createForm] = Form.useForm<CreateAgentFormValues>()
  const [bindForm] = Form.useForm<BindToolFormValues>()
  const [promptForm] = Form.useForm<PromptFormValues>()
  const [promptPreviewForm] = Form.useForm<PromptPreviewValues>()
  const promptTemplateValue = Form.useWatch('template', promptForm)
  const promptVariablesValue = Form.useWatch('variables', promptForm)
  const promptPreviewValues = Form.useWatch([], promptPreviewForm)

  useEffect(() => {
    const container = chatScrollRef.current
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  }, [chatMessages])

  useEffect(
    () => () => {
      streamAbortRef.current?.abort()
      if (flushTimerRef.current) {
        window.clearTimeout(flushTimerRef.current)
      }
    },
    []
  )

  const agentsQuery = useQuery({
    queryKey: ['p5-agents', projectId],
    queryFn: () => listAgents(projectId!),
    enabled: !!projectId,
  })

  const modelsQuery = useQuery({
    queryKey: ['p5-agent-models', projectId],
    queryFn: () => listInferenceModels(projectId!),
    enabled: !!projectId,
  })

  const agents = useMemo(() => agentsQuery.data?.items ?? [], [agentsQuery.data?.items])
  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgentId) ?? agents[0],
    [agents, selectedAgentId]
  )
  const boundToolCount = agents.reduce((total, agent) => total + (agent.tools?.length ?? 0), 0)

  const toolsQuery = useQuery({
    queryKey: ['p5-agent-tools', projectId, selectedToolAgent?.id],
    queryFn: () => listAgentTools(projectId!, selectedToolAgent!.id!),
    enabled: !!projectId && !!selectedToolAgent?.id && bindOpen,
  })

  const promptsQuery = useQuery({
    queryKey: ['p5-agent-prompts', projectId, selectedAgent?.id],
    queryFn: () => listPromptTemplates(projectId!, selectedAgent!.id!),
    enabled: !!projectId && !!selectedAgent?.id,
  })

  const historyQuery = useQuery({
    queryKey: ['p5-agent-history', projectId, selectedAgent?.id, conversationId],
    queryFn: () =>
      getChatHistory(projectId!, selectedAgent!.id!, {
        conversationId: conversationId.trim() || undefined,
        page: 1,
        pageSize: 50,
      }),
    enabled: !!projectId && !!selectedAgent?.id && !!conversationId.trim(),
  })

  const modelOptions = useMemo(
    () =>
      (modelsQuery.data?.items ?? []).map((model) => ({
        label: modelLabel(model),
        value: model.id,
      })),
    [modelsQuery.data?.items]
  )

  const agentOptions = useMemo(
    () =>
      agents.map((agent) => ({
        label: agent.name ?? agent.id,
        value: agent.id,
      })),
    [agents]
  )

  const historyMessages = useMemo(
    () => historyQuery.data?.messages ?? historyQuery.data?.items ?? [],
    [historyQuery.data?.items, historyQuery.data?.messages]
  )
  const activePromptVariables = useMemo(
    () =>
      Array.from(
        new Set(
          parseVariables(promptVariablesValue).concat(extractTemplateVariables(promptTemplateValue))
        )
      ),
    [promptTemplateValue, promptVariablesValue]
  )
  const promptPreviewText = useMemo(
    () =>
      renderPromptPreview(promptTemplateValue ?? '', {
        prediction: promptPreviewValues?.prediction ?? '轻微异常',
        confidence: promptPreviewValues?.confidence ?? '87.3%',
        context: promptPreviewValues?.context ?? '最近一批商品图片中有 3 个样本边缘遮挡。',
      }),
    [
      promptPreviewValues?.confidence,
      promptPreviewValues?.context,
      promptPreviewValues?.prediction,
      promptTemplateValue,
    ]
  )

  const createMutation = useMutation({
    mutationFn: (values: CreateAgentFormValues) =>
      createAgent(projectId!, {
        name: values.name,
        description: values.description,
        system_prompt: values.system_prompt,
        model_config: {
          provider: values.provider,
          model: values.model,
          temperature: values.temperature,
          max_tokens: values.max_tokens,
        },
      }),
    onSuccess: (agent) => {
      queryClient.invalidateQueries({ queryKey: ['p5-agents', projectId] })
      if (agent.id) {
        setSelectedAgentId(agent.id)
      }
      setCreateOpen(false)
      createForm.resetFields()
      messageApi.success('Agent 创建成功')
    },
    onError: () => {
      messageApi.error('Agent 创建失败')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (agentId: string) => deleteAgent(projectId!, agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['p5-agents', projectId] })
      messageApi.success('Agent 已删除')
    },
    onError: () => {
      messageApi.error('Agent 删除失败')
    },
  })

  const bindMutation = useMutation({
    mutationFn: (values: BindToolFormValues) => {
      if (!selectedToolAgent?.id) {
        return Promise.reject(new Error('missing agent'))
      }
      return bindAgentTools(projectId!, selectedToolAgent.id, {
        tools: [
          {
            name: values.name,
            type: 'model_inference',
            model_id: values.model_id,
            description: values.description,
          },
        ],
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['p5-agents', projectId] })
      queryClient.invalidateQueries({
        queryKey: ['p5-agent-tools', projectId, selectedToolAgent?.id],
      })
      bindForm.resetFields()
      setBindOpen(false)
      messageApi.success('工具绑定成功')
    },
    onError: () => {
      messageApi.error('工具绑定失败')
    },
  })

  const promptMutation = useMutation({
    mutationFn: (values: PromptFormValues) => {
      if (!selectedAgent?.id) {
        return Promise.reject(new Error('missing agent'))
      }
      const payload: PromptTemplateCreate = {
        name: values.name,
        description: values.description,
        template: values.template,
        variables: parseVariables(values.variables),
      }
      return savePromptTemplate(projectId!, selectedAgent.id, payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['p5-agent-prompts', projectId, selectedAgent?.id],
      })
      promptForm.resetFields()
      messageApi.success('Prompt 模板已保存')
    },
    onError: () => {
      messageApi.error('Prompt 模板保存失败')
    },
  })

  const openCreateModal = useCallback(() => {
    createForm.resetFields()
    setCreateOpen(true)
  }, [createForm])

  const openBindModal = useCallback(
    (agent: Agent) => {
      setSelectedToolAgent(agent)
      bindForm.setFieldsValue({
        name: 'model_predict',
        description: '调用已训练模型执行推理',
      })
      setBindOpen(true)
    },
    [bindForm]
  )

  const loadPromptTemplate = useCallback(
    (template: PromptTemplate) => {
      promptForm.setFieldsValue({
        name: template.name,
        description: template.description,
        template: template.template ?? '',
        variables: template.variables?.join(', '),
      })
      messageApi.success('已加载 Prompt 模板')
    },
    [messageApi, promptForm]
  )

  const flushAssistantBuffer = useCallback(() => {
    if (!tokenBufferRef.current) {
      return
    }
    const text = tokenBufferRef.current
    tokenBufferRef.current = ''
    if (flushTimerRef.current) {
      window.clearTimeout(flushTimerRef.current)
      flushTimerRef.current = undefined
    }
    setChatMessages((items) => appendLatestAssistantMessage(items, text))
  }, [])

  const appendAssistantText = useCallback(
    (text: string) => {
      if (!text) {
        return
      }
      tokenBufferRef.current += text
      if (!flushTimerRef.current) {
        flushTimerRef.current = window.setTimeout(flushAssistantBuffer, 48)
      }
    },
    [flushAssistantBuffer]
  )

  const pushToolEvent = useCallback((item: Omit<ToolTimelineItem, 'id'>) => {
    setToolEvents((items) => [
      ...items.slice(-(MAX_TOOL_EVENTS - 1)),
      {
        ...item,
        id: `${item.type}-${Date.now()}-${items.length}`,
      },
    ])
  }, [])

  const handleStreamEvent = useCallback(
    (event: AgentStreamEvent) => {
      if (event.type === 'token' || event.type === 'content') {
        appendAssistantText(getEventText(event))
        return
      }

      if (event.type === 'tool_call') {
        flushAssistantBuffer()
        pushToolEvent({
          type: 'tool_call',
          name: event.name ?? event.tool,
          detail: event.args,
        })
        return
      }

      if (event.type === 'tool_result') {
        flushAssistantBuffer()
        pushToolEvent({
          type: 'tool_result',
          name: event.name ?? event.tool,
          detail: event.result,
        })
        return
      }

      if (event.type === 'error') {
        flushAssistantBuffer()
        pushToolEvent({
          type: 'error',
          name: 'agent',
          detail: getEventText(event) || event.result,
        })
      }
    },
    [appendAssistantText, flushAssistantBuffer, pushToolEvent]
  )

  const sendChatMessage = useCallback(async () => {
    if (!projectId || !selectedAgent?.id || !chatInput.trim()) {
      messageApi.warning('请选择 Agent 并输入消息')
      return
    }

    flushAssistantBuffer()
    const content = chatInput.trim()
    const assistantId = `assistant-${Date.now()}`
    const controller = new AbortController()
    streamAbortRef.current = controller
    setStreaming(true)
    setChatInput('')
    setChatMessages((items) => [
      ...items,
      { id: `user-${Date.now()}`, role: 'user', content },
      { id: assistantId, role: 'assistant', content: '' },
    ])

    try {
      await streamAgentChat(
        projectId,
        selectedAgent.id,
        {
          message: content,
          conversation_id: getChatConversationId(conversationId),
          stream: true,
        },
        {
          signal: controller.signal,
          onEvent: (event) => {
            if (event.conversation_id) {
              setConversationId(event.conversation_id)
            }
            handleStreamEvent(event)
          },
        }
      )
      flushAssistantBuffer()
      queryClient.invalidateQueries({ queryKey: ['p5-agent-history', projectId, selectedAgent.id] })
      messageApi.success('Agent 回复完成')
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        flushAssistantBuffer()
        messageApi.info('已停止生成')
      } else {
        flushAssistantBuffer()
        setChatMessages((items) =>
          appendLatestAssistantMessage(items, '\n[对话请求失败，请稍后重试]')
        )
        messageApi.error('Agent 对话失败')
      }
    } finally {
      setStreaming(false)
      streamAbortRef.current = undefined
    }
  }, [
    chatInput,
    conversationId,
    flushAssistantBuffer,
    handleStreamEvent,
    messageApi,
    projectId,
    queryClient,
    selectedAgent,
  ])

  const stopStreaming = useCallback(() => {
    streamAbortRef.current?.abort()
  }, [])

  const clearChat = useCallback(() => {
    flushAssistantBuffer()
    setChatMessages([])
    setToolEvents([])
  }, [flushAssistantBuffer])

  const columns = useMemo(
    () => [
      {
        title: 'Agent',
        key: 'agent',
        width: 300,
        render: (_value: unknown, agent: Agent) => (
          <Space direction="vertical" size={4} style={{ maxWidth: 280 }}>
            <Text
              strong
              style={{ fontSize: 15, lineHeight: '22px' }}
              ellipsis={{ tooltip: agent.name }}
            >
              {agent.name}
            </Text>
            <Text
              type="secondary"
              style={{ fontSize: 13, lineHeight: '20px' }}
              ellipsis={{ tooltip: agent.description || '暂无描述' }}
            >
              {agent.description || '暂无描述'}
            </Text>
          </Space>
        ),
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 96,
        render: (status?: Agent['status']) => (
          <Tag color={agentStatusColor(status)} style={{ marginInlineEnd: 0 }}>
            {agentStatusLabel(status)}
          </Tag>
        ),
      },
      {
        title: '模型配置',
        key: 'model_config',
        width: 210,
        render: (_value: unknown, agent: Agent) => (
          <Space direction="vertical" size={2} style={{ maxWidth: 190 }}>
            <Text style={{ fontSize: 13 }} ellipsis={{ tooltip: getAgentModelName(agent) }}>
              {getAgentModelName(agent)}
            </Text>
            <Text
              type="secondary"
              style={{ fontSize: 12 }}
              ellipsis={{ tooltip: getAgentProviderName(agent) }}
            >
              {getAgentProviderName(agent)}
            </Text>
          </Space>
        ),
      },
      {
        title: '工具',
        dataIndex: 'tools',
        key: 'tools',
        width: 230,
        render: (tools?: AgentTool[]) => renderCompactToolTags(tools),
      },
      {
        title: '更新时间',
        dataIndex: 'updated_at',
        key: 'updated_at',
        width: 170,
        render: (value?: string) => (
          <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
            {formatDate(value)}
          </Text>
        ),
      },
      {
        title: '操作',
        key: 'actions',
        width: 212,
        render: (_value: unknown, agent: Agent) => (
          <Space size={8} wrap>
            <Button
              size="small"
              icon={<SendOutlined />}
              onClick={() => setSelectedAgentId(agent.id)}
            >
              对话
            </Button>
            <Button size="small" icon={<LinkOutlined />} onClick={() => openBindModal(agent)}>
              绑定
            </Button>
            <Popconfirm
              title="删除 Agent"
              description="确认删除该 Agent？"
              onConfirm={() => agent.id && deleteMutation.mutate(agent.id)}
            >
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                loading={deleteMutation.isPending}
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [deleteMutation, openBindModal]
  )

  const managementPanel = useMemo(
    () => (
      <Row gutter={[16, 16]}>
        <Col xs={24} xl={17}>
          <Card
            title={
              <Space direction="vertical" size={0}>
                <Text strong style={{ fontSize: 16 }}>
                  Agent 列表
                </Text>
                <Text type="secondary" style={{ fontSize: 12, fontWeight: 400 }}>
                  管理当前项目中的 Agent、模型配置和已绑定工具
                </Text>
              </Space>
            }
            styles={{ body: { paddingTop: 12 } }}
          >
            <Table
              rowKey={(agent) => agent.id ?? agent.name ?? 'agent'}
              columns={columns}
              dataSource={agents}
              loading={agentsQuery.isLoading}
              pagination={{ pageSize: 8 }}
              size="middle"
              tableLayout="fixed"
              scroll={{ x: 1220 }}
              locale={{
                emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无 Agent" />,
              }}
            />
          </Card>
        </Col>
        <Col xs={24} xl={7}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Card
              title={
                <Text strong style={{ fontSize: 16 }}>
                  运行概览
                </Text>
              }
              styles={{ body: { paddingTop: 12 } }}
            >
              <Row gutter={[12, 12]}>
                <Col span={12}>
                  <Statistic
                    title={<Text type="secondary">Agent 数量</Text>}
                    value={agents.length}
                    valueStyle={{ fontSize: 24, lineHeight: '32px' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title={<Text type="secondary">绑定工具</Text>}
                    value={boundToolCount}
                    valueStyle={{ fontSize: 24, lineHeight: '32px' }}
                  />
                </Col>
              </Row>
            </Card>
            <Card
              title={
                <Space direction="vertical" size={0}>
                  <Text strong style={{ fontSize: 16 }}>
                    当前 Agent
                  </Text>
                  <Text type="secondary" style={{ fontSize: 12, fontWeight: 400 }}>
                    {selectedAgent?.name ?? '未选择 Agent'}
                  </Text>
                </Space>
              }
              styles={{ body: { paddingTop: 12 } }}
            >
              <Descriptions
                column={1}
                size="small"
                labelStyle={{ width: 76, color: '#595959', fontSize: 13 }}
                contentStyle={{ fontSize: 13 }}
              >
                <Descriptions.Item label="状态">
                  <Tag color={agentStatusColor(selectedAgent?.status)}>
                    {agentStatusLabel(selectedAgent?.status)}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Provider">
                  <Text ellipsis={{ tooltip: getAgentProviderName(selectedAgent) }}>
                    {getAgentProviderName(selectedAgent)}
                  </Text>
                </Descriptions.Item>
                <Descriptions.Item label="LLM 模型">
                  <Text ellipsis={{ tooltip: getAgentModelName(selectedAgent) }}>
                    {getAgentModelName(selectedAgent)}
                  </Text>
                </Descriptions.Item>
                <Descriptions.Item label="温度">
                  {getAgentConfigValue(selectedAgent, 'temperature')}
                </Descriptions.Item>
                <Descriptions.Item label="Token">
                  {getAgentConfigValue(selectedAgent, 'max_tokens')}
                </Descriptions.Item>
                <Descriptions.Item label="工具">
                  {renderToolTags(selectedAgent?.tools)}
                </Descriptions.Item>
              </Descriptions>
              <div style={{ marginTop: 12 }}>
                <Text type="secondary" style={{ display: 'block', marginBottom: 6, fontSize: 13 }}>
                  系统提示词
                </Text>
                <Paragraph
                  ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
                  style={{
                    marginBottom: 0,
                    color: '#262626',
                    fontSize: 13,
                    lineHeight: '20px',
                    background: '#fafafa',
                    border: '1px solid #f0f0f0',
                    borderRadius: 8,
                    padding: '8px 10px',
                  }}
                >
                  {selectedAgent?.system_prompt || '暂无系统提示词'}
                </Paragraph>
              </div>
            </Card>
          </Space>
        </Col>
      </Row>
    ),
    [agents, agentsQuery.isLoading, boundToolCount, columns, selectedAgent]
  )

  const chatPanel = useMemo(
    () => (
      <Row gutter={[16, 16]}>
        <Col xs={24} xl={7}>
          <Card title="对话配置">
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              <Select
                style={{ width: '100%' }}
                placeholder="选择 Agent"
                value={selectedAgent?.id}
                options={agentOptions}
                loading={agentsQuery.isLoading}
                onChange={setSelectedAgentId}
              />
              <Input
                value={conversationId}
                onChange={(event) => setConversationId(event.target.value)}
                placeholder="conversation_id"
                disabled={streaming}
              />
              <Descriptions bordered size="small" column={1}>
                <Descriptions.Item label="状态">
                  <Tag color={agentStatusColor(selectedAgent?.status)}>
                    {selectedAgent?.status ?? '-'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="模型">
                  {getAgentModelName(selectedAgent)}
                </Descriptions.Item>
                <Descriptions.Item label="工具">
                  {renderToolTags(selectedAgent?.tools)}
                </Descriptions.Item>
              </Descriptions>
            </Space>
          </Card>
          <Card title="工具调用" style={{ marginTop: 16 }}>
            <ToolTimeline items={toolEvents} />
          </Card>
        </Col>
        <Col xs={24} xl={17}>
          <Card
            title="Agent 对话"
            extra={
              streaming ? (
                <Tag color="processing">流式响应中</Tag>
              ) : (
                <Tag color={selectedAgent ? 'green' : 'default'}>
                  {selectedAgent ? '就绪' : '未选择 Agent'}
                </Tag>
              )
            }
          >
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              <div
                ref={chatScrollRef}
                style={{
                  minHeight: 360,
                  maxHeight: 520,
                  overflow: 'auto',
                  padding: '4px 8px 4px 0',
                  scrollBehavior: 'smooth',
                }}
              >
                <ChatMessages messages={chatMessages} />
              </div>
              <Input.TextArea
                rows={4}
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                placeholder="输入要交给 Agent 分析的问题"
                disabled={streaming}
              />
              <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                <Button
                  onClick={clearChat}
                  disabled={streaming || (chatMessages.length === 0 && toolEvents.length === 0)}
                >
                  清空对话
                </Button>
                <Space>
                  <Button icon={<StopOutlined />} onClick={stopStreaming} disabled={!streaming}>
                    停止
                  </Button>
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    loading={streaming}
                    onClick={sendChatMessage}
                    disabled={!selectedAgent || !chatInput.trim()}
                  >
                    发送
                  </Button>
                </Space>
              </Space>
            </Space>
          </Card>
        </Col>
      </Row>
    ),
    [
      agentOptions,
      agentsQuery.isLoading,
      chatInput,
      chatMessages,
      conversationId,
      clearChat,
      selectedAgent,
      sendChatMessage,
      stopStreaming,
      streaming,
      toolEvents,
    ]
  )

  const historyPanel = useMemo(
    () => (
      <Row gutter={[16, 16]}>
        <Col xs={24} xl={7}>
          <Card title="日志筛选">
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              <Select
                style={{ width: '100%' }}
                placeholder="选择 Agent"
                value={selectedAgent?.id}
                options={agentOptions}
                loading={agentsQuery.isLoading}
                onChange={setSelectedAgentId}
              />
              <Input
                value={conversationId}
                onChange={(event) => setConversationId(event.target.value)}
                placeholder="输入 conversation_id"
              />
              <Button
                block
                icon={<ReloadOutlined />}
                onClick={() => historyQuery.refetch()}
                loading={historyQuery.isFetching}
                disabled={!selectedAgent || !conversationId.trim()}
              >
                刷新日志
              </Button>
              <Descriptions bordered column={1} size="small">
                <Descriptions.Item label="消息数">
                  {historyQuery.data?.total ?? historyMessages.length}
                </Descriptions.Item>
                <Descriptions.Item label="会话 ID">
                  {historyQuery.data?.conversation_id ?? conversationId}
                </Descriptions.Item>
              </Descriptions>
            </Space>
          </Card>
        </Col>
        <Col xs={24} xl={17}>
          <Card
            title="对话日志"
            extra={
              <Tag color={historyQuery.isFetching ? 'processing' : 'default'}>
                {historyMessages.length} 条消息
              </Tag>
            }
          >
            <HistoryMessages messages={historyMessages} />
          </Card>
        </Col>
      </Row>
    ),
    [
      agentOptions,
      agentsQuery.isLoading,
      conversationId,
      historyMessages,
      historyQuery,
      selectedAgent,
    ]
  )

  const promptPanel = useMemo(
    () => (
      <Row gutter={[16, 16]}>
        <Col xs={24} xl={10}>
          <Card title="Prompt 编辑器">
            <Form<PromptFormValues>
              form={promptForm}
              layout="vertical"
              initialValues={{
                name: '模型结果解释模板',
                template:
                  '请基于 $prediction、$confidence 和 $context，生成面向业务人员的推理结果解释与下一步建议。',
                variables: 'prediction, confidence, context',
              }}
              onFinish={(values) => promptMutation.mutate(values)}
            >
              <Form.Item
                name="name"
                label="名称"
                rules={[{ required: true, message: '请输入模板名称' }]}
              >
                <Input />
              </Form.Item>
              <Form.Item name="description" label="描述">
                <Input />
              </Form.Item>
              <Form.Item name="variables" label="变量">
                <Input placeholder="prediction, confidence, context" />
              </Form.Item>
              <Form.Item
                name="template"
                label="模板内容"
                rules={[{ required: true, message: '请输入模板内容' }]}
              >
                <Input.TextArea rows={9} />
              </Form.Item>
              <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                <Space size={[0, 8]} wrap>
                  {activePromptVariables.map((variable) => (
                    <Tag key={variable}>{variable}</Tag>
                  ))}
                </Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={promptMutation.isPending}
                  disabled={!selectedAgent}
                >
                  保存模板
                </Button>
              </Space>
            </Form>
          </Card>
          <Card title="变量预览" style={{ marginTop: 16 }}>
            <Form<PromptPreviewValues>
              form={promptPreviewForm}
              layout="vertical"
              initialValues={{
                prediction: '轻微异常',
                confidence: '87.3%',
                context: '最近一批商品图片中有 3 个样本边缘遮挡。',
              }}
            >
              <Form.Item name="prediction" label="prediction">
                <Input />
              </Form.Item>
              <Form.Item name="confidence" label="confidence">
                <Input />
              </Form.Item>
              <Form.Item name="context" label="context">
                <Input.TextArea rows={3} />
              </Form.Item>
            </Form>
            <Paragraph
              style={{
                whiteSpace: 'pre-wrap',
                marginBottom: 0,
                padding: 12,
                border: '1px solid #d9d9d9',
                borderRadius: 8,
                background: '#fafafa',
              }}
            >
              {promptPreviewText || '填写模板内容后显示渲染预览'}
            </Paragraph>
          </Card>
        </Col>
        <Col xs={24} xl={14}>
          <Card title="Prompt 模板列表">
            <List
              loading={promptsQuery.isLoading}
              dataSource={promptsQuery.data ?? []}
              locale={{
                emptyText: (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无 Prompt 模板" />
                ),
              }}
              renderItem={(item: PromptTemplate) => (
                <List.Item
                  actions={[
                    <Button key="load" size="small" onClick={() => loadPromptTemplate(item)}>
                      加载
                    </Button>,
                  ]}
                >
                  <Space direction="vertical" size={6} style={{ width: '100%' }}>
                    <Space style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text strong>{item.name}</Text>
                      <Text type="secondary">{formatDate(item.updated_at ?? item.created_at)}</Text>
                    </Space>
                    <Text type="secondary">{item.description || '暂无描述'}</Text>
                    <Paragraph code style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                      {item.template}
                    </Paragraph>
                    <Space size={[0, 8]} wrap>
                      {(item.variables ?? []).map((variable) => (
                        <Tag key={variable}>{variable}</Tag>
                      ))}
                    </Space>
                  </Space>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    ),
    [
      activePromptVariables,
      loadPromptTemplate,
      promptForm,
      promptMutation,
      promptPreviewForm,
      promptPreviewText,
      promptsQuery.data,
      promptsQuery.isLoading,
      selectedAgent,
    ]
  )

  const tabItems = useMemo(
    () => [
      {
        key: 'manage',
        label: '管理',
        children: managementPanel,
      },
      {
        key: 'chat',
        label: '对话',
        children: chatPanel,
      },
      {
        key: 'history',
        label: '对话日志',
        children: historyPanel,
      },
      {
        key: 'prompts',
        label: 'Prompt 模板',
        children: promptPanel,
      },
    ],
    [chatPanel, historyPanel, managementPanel, promptPanel]
  )

  return (
    <div>
      {contextHolder}
      <Space
        style={{ width: '100%', justifyContent: 'space-between', marginBottom: 20 }}
        align="start"
      >
        <Space direction="vertical" size={4}>
          <h2 style={{ margin: 0 }}>Agent 工作区</h2>
          <Text type="secondary">管理 Agent、绑定推理工具，并用流式对话验证业务解释能力。</Text>
        </Space>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => agentsQuery.refetch()}
            loading={agentsQuery.isFetching}
          >
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
            创建 Agent
          </Button>
        </Space>
      </Space>

      {!projectId && (
        <Alert type="warning" showIcon message="未选择项目" style={{ marginBottom: 16 }} />
      )}

      <Tabs items={tabItems} />

      <Modal
        title="创建 Agent"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => createForm.submit()}
        confirmLoading={createMutation.isPending}
        destroyOnClose
      >
        <Form<CreateAgentFormValues>
          form={createForm}
          layout="vertical"
          initialValues={{
            provider: 'mock',
            model: 'deepflow-mock-agent',
            temperature: 0.4,
            max_tokens: 2048,
          }}
          onFinish={(values) => createMutation.mutate(values)}
        >
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入 Agent 名称' }]}
          >
            <Input placeholder="商品质检助手" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input placeholder="用于推理结果解释与质检报告生成" />
          </Form.Item>
          <Form.Item name="system_prompt" label="系统提示词">
            <Input.TextArea rows={4} placeholder="你是一个严谨的业务分析助手..." />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item
                name="provider"
                label="Provider"
                rules={[{ required: true, message: '请选择 Provider' }]}
              >
                <Select
                  options={[
                    { label: 'Mock', value: 'mock' },
                    { label: 'OpenAI', value: 'openai' },
                    { label: 'Azure', value: 'azure' },
                    { label: 'Anthropic', value: 'anthropic' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="model"
                label="LLM 模型"
                rules={[{ required: true, message: '请输入模型名称' }]}
              >
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item
                name="temperature"
                label="Temperature"
                rules={[{ required: true, message: '请输入温度' }]}
              >
                <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="max_tokens"
                label="Max Tokens"
                rules={[{ required: true, message: '请输入最大 Token 数' }]}
              >
                <InputNumber min={128} max={8192} step={128} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      <Modal
        title={selectedToolAgent?.name ? `绑定工具 - ${selectedToolAgent.name}` : '绑定工具'}
        open={bindOpen}
        onCancel={() => setBindOpen(false)}
        onOk={() => bindForm.submit()}
        confirmLoading={bindMutation.isPending}
        destroyOnClose
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <div>
            <Text strong>已绑定工具</Text>
            <div style={{ marginTop: 8 }}>
              {toolsQuery.data?.length ? (
                renderToolTags(toolsQuery.data)
              ) : (
                <Text type="secondary">暂无工具</Text>
              )}
            </div>
          </div>
          <Form<BindToolFormValues>
            form={bindForm}
            layout="vertical"
            onFinish={(values) => bindMutation.mutate(values)}
          >
            <Form.Item
              name="model_id"
              label="模型"
              rules={[{ required: true, message: '请选择模型' }]}
            >
              <Select
                loading={modelsQuery.isLoading}
                options={modelOptions}
                placeholder="选择模型"
              />
            </Form.Item>
            <Form.Item
              name="name"
              label="工具名称"
              rules={[{ required: true, message: '请输入工具名称' }]}
            >
              <Input />
            </Form.Item>
            <Form.Item name="description" label="描述">
              <Input.TextArea rows={3} />
            </Form.Item>
          </Form>
        </Space>
      </Modal>
    </div>
  )
}
