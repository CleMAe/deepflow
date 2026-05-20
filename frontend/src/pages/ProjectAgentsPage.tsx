import { useMemo, useRef, useState } from 'react'
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
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd'
import { DeleteOutlined, LinkOutlined, PlusOutlined, ReloadOutlined, SendOutlined, StopOutlined } from '@ant-design/icons'
import {
  bindAgentTools,
  createAgent,
  deleteAgent,
  listAgentTools,
  listAgents,
  listPromptTemplates,
  savePromptTemplate,
  streamAgentChat,
  type Agent,
  type AgentCreate,
  type AgentStreamEvent,
  type AgentTool,
  type PromptTemplate,
  type PromptTemplateCreate,
} from '@/api/agents'
import { listInferenceModels, type Model } from '@/api/inference'

const { Paragraph, Text } = Typography

type AgentModelConfig = NonNullable<AgentCreate['model_config']>
type AgentProvider = AgentModelConfig['provider']
type ChatRole = 'user' | 'assistant'
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

function modelLabel(model: Model) {
  return `${model.name ?? model.id} · ${model.arch_type ?? 'custom'}`
}

function agentStatusColor(status?: Agent['status']) {
  return status === 'active' ? 'green' : 'default'
}

function getAgentModelName(agent?: Agent) {
  const config = agent?.model_config ?? {}
  return String(config.model ?? 'mock')
}

function getEventText(event: AgentStreamEvent) {
  return event.content ?? event.text ?? ''
}

function renderToolTags(tools?: AgentTool[]) {
  if (!tools?.length) {
    return <Text type="secondary">未绑定</Text>
  }

  return (
    <Space size={[0, 8]} wrap>
      {tools.map((tool) => (
        <Tag key={tool.tool_id ?? tool.name} color={tool.type === 'model_inference' ? 'blue' : 'default'}>
          {tool.name}
        </Tag>
      ))}
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
              <Tag color={item.type === 'tool_call' ? 'blue' : item.type === 'tool_result' ? 'green' : 'red'}>
                {item.type === 'tool_call' ? '工具调用' : item.type === 'tool_result' ? '工具结果' : '错误'}
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

export default function ProjectAgentsPage() {
  const { projectId } = useParams()
  const queryClient = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  const [createOpen, setCreateOpen] = useState(false)
  const [bindOpen, setBindOpen] = useState(false)
  const [selectedAgentId, setSelectedAgentId] = useState<string>()
  const [selectedToolAgent, setSelectedToolAgent] = useState<Agent>()
  const [chatInput, setChatInput] = useState('请结合已绑定模型工具，分析最近一次批量推理中的异常样本。')
  const [chatMessages, setChatMessages] = useState<LocalChatMessage[]>([])
  const [toolEvents, setToolEvents] = useState<ToolTimelineItem[]>([])
  const [streaming, setStreaming] = useState(false)
  const streamAbortRef = useRef<AbortController>()
  const [createForm] = Form.useForm<CreateAgentFormValues>()
  const [bindForm] = Form.useForm<BindToolFormValues>()
  const [promptForm] = Form.useForm<PromptFormValues>()

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
      queryClient.invalidateQueries({ queryKey: ['p5-agent-tools', projectId, selectedToolAgent?.id] })
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
        variables: values.variables
          ?.split(',')
          .map((item) => item.trim())
          .filter(Boolean),
      }
      return savePromptTemplate(projectId!, selectedAgent.id, payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['p5-agent-prompts', projectId, selectedAgent?.id] })
      promptForm.resetFields()
      messageApi.success('Prompt 模板已保存')
    },
    onError: () => {
      messageApi.error('Prompt 模板保存失败')
    },
  })

  const openCreateModal = () => {
    createForm.resetFields()
    setCreateOpen(true)
  }

  const openBindModal = (agent: Agent) => {
    setSelectedToolAgent(agent)
    bindForm.setFieldsValue({
      name: 'model_predict',
      description: '调用已训练模型执行推理',
    })
    setBindOpen(true)
  }

  const appendAssistantText = (text: string) => {
    setChatMessages((items) =>
      items.map((item, index) =>
        index === items.length - 1 && item.role === 'assistant'
          ? { ...item, content: `${item.content}${text}` }
          : item
      )
    )
  }

  const handleStreamEvent = (event: AgentStreamEvent) => {
    if (event.type === 'token' || event.type === 'content') {
      appendAssistantText(getEventText(event))
      return
    }

    if (event.type === 'tool_call') {
      setToolEvents((items) => [
        ...items,
        {
          id: `tool-call-${items.length}-${Date.now()}`,
          type: 'tool_call',
          name: event.name ?? event.tool,
          detail: event.args,
        },
      ])
      return
    }

    if (event.type === 'tool_result') {
      setToolEvents((items) => [
        ...items,
        {
          id: `tool-result-${items.length}-${Date.now()}`,
          type: 'tool_result',
          name: event.name ?? event.tool,
          detail: event.result,
        },
      ])
      return
    }

    if (event.type === 'error') {
      setToolEvents((items) => [
        ...items,
        {
          id: `tool-error-${items.length}-${Date.now()}`,
          type: 'error',
          name: 'agent',
          detail: getEventText(event) || event.result,
        },
      ])
    }
  }

  const sendChatMessage = async () => {
    if (!projectId || !selectedAgent?.id || !chatInput.trim()) {
      messageApi.warning('请选择 Agent 并输入消息')
      return
    }

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
          stream: true,
        },
        {
          signal: controller.signal,
          onEvent: (event) => {
            handleStreamEvent(event)
          },
        }
      )
      messageApi.success('Agent 回复完成')
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        messageApi.info('已停止生成')
      } else {
        appendAssistantText('\n[对话请求失败，请稍后重试]')
        messageApi.error('Agent 对话失败')
      }
    } finally {
      setStreaming(false)
      streamAbortRef.current = undefined
    }
  }

  const stopStreaming = () => {
    streamAbortRef.current?.abort()
  }

  const columns = [
    {
      title: 'Agent',
      key: 'agent',
      render: (_value: unknown, agent: Agent) => (
        <Space direction="vertical" size={2}>
          <Text strong>{agent.name}</Text>
          <Text type="secondary">{agent.description || '暂无描述'}</Text>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 96,
      render: (status?: Agent['status']) => <Tag color={agentStatusColor(status)}>{status ?? 'inactive'}</Tag>,
    },
    {
      title: '模型配置',
      key: 'model_config',
      render: (_value: unknown, agent: Agent) => <Text>{getAgentModelName(agent)}</Text>,
    },
    {
      title: '工具',
      dataIndex: 'tools',
      key: 'tools',
      render: (tools?: AgentTool[]) => renderToolTags(tools),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
      render: (value?: string) => formatDate(value),
    },
    {
      title: '操作',
      key: 'actions',
      width: 220,
      render: (_value: unknown, agent: Agent) => (
        <Space>
          <Button size="small" icon={<SendOutlined />} onClick={() => setSelectedAgentId(agent.id)}>
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
            <Button size="small" danger icon={<DeleteOutlined />} loading={deleteMutation.isPending}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const managementPanel = (
    <Row gutter={[16, 16]}>
      <Col xs={24} xl={17}>
        <Card title="Agent 列表">
          <Table
            rowKey={(agent) => agent.id ?? agent.name ?? 'agent'}
            columns={columns}
            dataSource={agents}
            loading={agentsQuery.isLoading}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无 Agent" /> }}
          />
        </Card>
      </Col>
      <Col xs={24} xl={7}>
        <Card title="运行概览">
          <Descriptions column={1} size="small">
            <Descriptions.Item label="Agent 数量">{agents.length}</Descriptions.Item>
            <Descriptions.Item label="绑定工具">{boundToolCount}</Descriptions.Item>
            <Descriptions.Item label="当前 Agent">{selectedAgent?.name ?? '-'}</Descriptions.Item>
            <Descriptions.Item label="LLM 模型">{getAgentModelName(selectedAgent)}</Descriptions.Item>
          </Descriptions>
        </Card>
      </Col>
    </Row>
  )

  const chatPanel = (
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
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label="状态">
                <Tag color={agentStatusColor(selectedAgent?.status)}>{selectedAgent?.status ?? '-'}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="模型">{getAgentModelName(selectedAgent)}</Descriptions.Item>
              <Descriptions.Item label="工具">{renderToolTags(selectedAgent?.tools)}</Descriptions.Item>
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
              <Tag color={selectedAgent ? 'green' : 'default'}>{selectedAgent ? '就绪' : '未选择 Agent'}</Tag>
            )
          }
        >
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <div style={{ minHeight: 360, maxHeight: 520, overflow: 'auto', paddingRight: 8 }}>
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
              <Button onClick={() => setChatMessages([])} disabled={streaming || chatMessages.length === 0}>
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
  )

  const promptPanel = (
    <Row gutter={[16, 16]}>
      <Col xs={24} xl={10}>
        <Card title="保存 Prompt 模板">
          <Form<PromptFormValues>
            form={promptForm}
            layout="vertical"
            initialValues={{
              name: '模型结果解释模板',
              template: '请基于 $prediction 和 $confidence 生成面向业务人员的解释。',
              variables: 'prediction, confidence',
            }}
            onFinish={(values) => promptMutation.mutate(values)}
          >
            <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入模板名称' }]}>
              <Input />
            </Form.Item>
            <Form.Item name="description" label="描述">
              <Input />
            </Form.Item>
            <Form.Item name="variables" label="变量">
              <Input placeholder="prediction, confidence" />
            </Form.Item>
            <Form.Item name="template" label="模板内容" rules={[{ required: true, message: '请输入模板内容' }]}>
              <Input.TextArea rows={8} />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={promptMutation.isPending} disabled={!selectedAgent}>
              保存模板
            </Button>
          </Form>
        </Card>
      </Col>
      <Col xs={24} xl={14}>
        <Card title="Prompt 模板列表">
          <List
            loading={promptsQuery.isLoading}
            dataSource={promptsQuery.data ?? []}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无 Prompt 模板" /> }}
            renderItem={(item: PromptTemplate) => (
              <List.Item>
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
  )

  return (
    <div>
      {contextHolder}
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 24 }} align="center">
        <h2 style={{ margin: 0 }}>Agent</h2>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => agentsQuery.refetch()} loading={agentsQuery.isFetching}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
            创建 Agent
          </Button>
        </Space>
      </Space>

      {!projectId && <Alert type="warning" showIcon message="未选择项目" style={{ marginBottom: 16 }} />}

      <Tabs
        items={[
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
            key: 'prompts',
            label: 'Prompt 模板',
            children: promptPanel,
          },
        ]}
      />

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
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入 Agent 名称' }]}>
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
              <Form.Item name="provider" label="Provider" rules={[{ required: true, message: '请选择 Provider' }]}>
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
              <Form.Item name="model" label="LLM 模型" rules={[{ required: true, message: '请输入模型名称' }]}>
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="temperature" label="Temperature" rules={[{ required: true, message: '请输入温度' }]}>
                <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="max_tokens" label="Max Tokens" rules={[{ required: true, message: '请输入最大 Token 数' }]}>
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
              {toolsQuery.data?.length ? renderToolTags(toolsQuery.data) : <Text type="secondary">暂无工具</Text>}
            </div>
          </div>
          <Form<BindToolFormValues> form={bindForm} layout="vertical" onFinish={(values) => bindMutation.mutate(values)}>
            <Form.Item name="model_id" label="模型" rules={[{ required: true, message: '请选择模型' }]}>
              <Select loading={modelsQuery.isLoading} options={modelOptions} placeholder="选择模型" />
            </Form.Item>
            <Form.Item name="name" label="工具名称" rules={[{ required: true, message: '请输入工具名称' }]}>
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
