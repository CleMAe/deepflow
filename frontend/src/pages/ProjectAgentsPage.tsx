import { useMemo, useState } from 'react'
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
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import { DeleteOutlined, LinkOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  bindAgentTools,
  createAgent,
  deleteAgent,
  listAgentTools,
  listAgents,
  type Agent,
  type AgentCreate,
  type AgentTool,
} from '@/api/agents'
import { listInferenceModels, type Model } from '@/api/inference'

const { Text } = Typography

type AgentModelConfig = NonNullable<AgentCreate['model_config']>
type AgentProvider = AgentModelConfig['provider']

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

function formatDate(value?: string) {
  if (!value) {
    return '-'
  }
  return new Date(value).toLocaleString()
}

function modelLabel(model: Model) {
  return `${model.name ?? model.id} · ${model.arch_type ?? 'custom'}`
}

function agentStatusColor(status?: Agent['status']) {
  return status === 'active' ? 'green' : 'default'
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

export default function ProjectAgentsPage() {
  const { projectId } = useParams()
  const queryClient = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  const [createOpen, setCreateOpen] = useState(false)
  const [bindOpen, setBindOpen] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState<Agent>()
  const [createForm] = Form.useForm<CreateAgentFormValues>()
  const [bindForm] = Form.useForm<BindToolFormValues>()

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

  const toolsQuery = useQuery({
    queryKey: ['p5-agent-tools', projectId, selectedAgent?.id],
    queryFn: () => listAgentTools(projectId!, selectedAgent!.id!),
    enabled: !!projectId && !!selectedAgent?.id && bindOpen,
  })

  const agents = agentsQuery.data?.items ?? []
  const boundToolCount = agents.reduce((total, agent) => total + (agent.tools?.length ?? 0), 0)

  const modelOptions = useMemo(
    () =>
      (modelsQuery.data?.items ?? []).map((model) => ({
        label: modelLabel(model),
        value: model.id,
      })),
    [modelsQuery.data?.items]
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['p5-agents', projectId] })
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
      if (!selectedAgent?.id) {
        return Promise.reject(new Error('missing agent'))
      }
      return bindAgentTools(projectId!, selectedAgent.id, {
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
      queryClient.invalidateQueries({ queryKey: ['p5-agent-tools', projectId, selectedAgent?.id] })
      bindForm.resetFields()
      setBindOpen(false)
      messageApi.success('工具绑定成功')
    },
    onError: () => {
      messageApi.error('工具绑定失败')
    },
  })

  const openCreateModal = () => {
    createForm.resetFields()
    setCreateOpen(true)
  }

  const openBindModal = (agent: Agent) => {
    setSelectedAgent(agent)
    bindForm.setFieldsValue({
      name: 'model_predict',
      description: '调用已训练模型执行推理',
    })
    setBindOpen(true)
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
      render: (_value: unknown, agent: Agent) => {
        const config = agent.model_config ?? {}
        return <Text>{String(config.model ?? 'mock')}</Text>
      },
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
      width: 180,
      render: (_value: unknown, agent: Agent) => (
        <Space>
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

  return (
    <div>
      {contextHolder}
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 24 }} align="center">
        <h2 style={{ margin: 0 }}>Agent 管理</h2>
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
              <Descriptions.Item label="模型来源">MSW Mock</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>

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
        title={selectedAgent?.name ? `绑定工具 - ${selectedAgent.name}` : '绑定工具'}
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
