import { useCallback, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  InputNumber,
  Row,
  Select,
  Space,
  Spin,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  CheckCircleOutlined,
  PlusOutlined,
  SearchOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import {
  createProjectModel,
  getModelLibraryDetail,
  listModelLibrary,
  listProjectModels,
  updateProjectModel,
  validateModelConfig,
  type LibraryModel,
  type Model,
  type ValidationResult,
} from '@/api/models'

const { Text, Paragraph } = Typography

type TaskType = NonNullable<LibraryModel['task_type']>
type ArchType = NonNullable<LibraryModel['arch_type']>

interface HyperparamFormValues {
  name: string
  description?: string
  num_classes?: number
  image_size?: number
  hidden_dims?: string
  output_dim?: number
  learning_rate: number
  optimizer: string
  loss_function: string
  batch_size: number
  epochs: number
  weight_decay: number
  device: string
}

const TASK_TYPE_OPTIONS: { label: string; value: TaskType | '' }[] = [
  { label: '全部任务', value: '' },
  { label: '分类', value: 'classification' },
  { label: '回归', value: 'regression' },
  { label: '目标检测', value: 'object_detection' },
  { label: '分割', value: 'segmentation' },
]

const OPTIMIZER_OPTIONS = ['sgd', 'adam', 'adamw', 'rmsprop'].map((v) => ({ label: v, value: v }))
const LOSS_OPTIONS = [
  'cross_entropy',
  'mse',
  'bce',
  'bce_with_logits',
  'nll',
  'l1',
  'huber',
].map((v) => ({ label: v, value: v }))
const DEVICE_OPTIONS = [
  { label: '自动', value: 'auto' },
  { label: 'CPU', value: 'cpu' },
  { label: 'CUDA', value: 'cuda' },
]

function formatParams(n?: number) {
  if (n === undefined) return '-'
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

function isImageArch(arch?: string) {
  return arch !== 'mlp' && arch !== 'custom'
}

function buildParamsCfg(values: HyperparamFormValues, archType?: string) {
  const base: Record<string, unknown> = {
    learning_rate: values.learning_rate,
    optimizer: values.optimizer,
    loss_function: values.loss_function,
    batch_size: values.batch_size,
    epochs: values.epochs,
    weight_decay: values.weight_decay,
    device: values.device,
  }
  if (isImageArch(archType)) {
    base.num_classes = values.num_classes
    base.image_size = values.image_size
  } else {
    base.hidden_dims = values.hidden_dims
      ?.split(',')
      .map((s) => Number(s.trim()))
      .filter((n) => !Number.isNaN(n))
    base.output_dim = values.output_dim
  }
  return base
}

function paramsCfgToForm(model?: Model): Partial<HyperparamFormValues> {
  const cfg = (model?.params_cfg ?? {}) as Record<string, unknown>
  const hidden = Array.isArray(cfg.hidden_dims) ? (cfg.hidden_dims as number[]).join(', ') : ''
  return {
    name: model?.name ?? '',
    description: model?.description,
    num_classes: typeof cfg.num_classes === 'number' ? cfg.num_classes : 10,
    image_size: typeof cfg.image_size === 'number' ? cfg.image_size : 224,
    hidden_dims: hidden || '128, 64',
    output_dim: typeof cfg.output_dim === 'number' ? cfg.output_dim : 1,
    learning_rate: typeof cfg.learning_rate === 'number' ? cfg.learning_rate : 0.001,
    optimizer: typeof cfg.optimizer === 'string' ? cfg.optimizer : 'adam',
    loss_function: typeof cfg.loss_function === 'string' ? cfg.loss_function : 'cross_entropy',
    batch_size: typeof cfg.batch_size === 'number' ? cfg.batch_size : 32,
    epochs: typeof cfg.epochs === 'number' ? cfg.epochs : 10,
    weight_decay: typeof cfg.weight_decay === 'number' ? cfg.weight_decay : 0,
    device: typeof cfg.device === 'string' ? cfg.device : 'auto',
  }
}

export default function ProjectModelsPage() {
  const { projectId = '' } = useParams()
  const queryClient = useQueryClient()
  const [form] = Form.useForm<HyperparamFormValues>()

  const [taskFilter, setTaskFilter] = useState<TaskType | ''>('')
  const [search, setSearch] = useState('')
  const [detailOpen, setDetailOpen] = useState(false)
  const [detailModel, setDetailModel] = useState<LibraryModel | null>(null)
  const [configOpen, setConfigOpen] = useState(false)
  const [editingModel, setEditingModel] = useState<Model | null>(null)
  const [validation, setValidation] = useState<ValidationResult | null>(null)

  const libraryQuery = useQuery({
    queryKey: ['model-library', taskFilter, search],
    queryFn: () =>
      listModelLibrary({
        task_type: taskFilter || undefined,
        search: search.trim() || undefined,
      }),
  })

  const projectModelsQuery = useQuery({
    queryKey: ['project-models', projectId],
    queryFn: () => listProjectModels(projectId),
    enabled: !!projectId,
  })

  const adoptMutation = useMutation({
    mutationFn: (lib: LibraryModel) =>
      createProjectModel(projectId, {
        name: `${lib.name} 配置`,
        arch_type: lib.arch_type as ArchType,
        params_cfg: lib.default_hyperparams,
        description: lib.description,
      }),
    onSuccess: () => {
      message.success('已添加到我的模型')
      void queryClient.invalidateQueries({ queryKey: ['project-models', projectId] })
    },
    onError: () => message.error('添加模型失败'),
  })

  const saveMutation = useMutation({
    mutationFn: (values: HyperparamFormValues) => {
      if (!editingModel?.id) throw new Error('no model')
      return updateProjectModel(projectId, editingModel.id, {
        name: values.name,
        description: values.description,
        params_cfg: buildParamsCfg(values, editingModel.arch_type),
      })
    },
    onSuccess: (model) => {
      message.success('配置已保存')
      setEditingModel(model)
      void queryClient.invalidateQueries({ queryKey: ['project-models', projectId] })
    },
    onError: () => message.error('保存失败'),
  })

  const validateMutation = useMutation({
    mutationFn: (values: HyperparamFormValues) => {
      if (!editingModel?.id) throw new Error('no model')
      return validateModelConfig(projectId, editingModel.id, {
        params_cfg: buildParamsCfg(values, editingModel.arch_type),
      })
    },
    onSuccess: (result) => {
      setValidation(result)
      if (result.valid) {
        message.success('参数校验通过')
      } else {
        message.warning('参数校验未通过，请查看提示')
      }
    },
    onError: () => message.error('校验请求失败'),
  })

  const openLibraryDetail = async (lib: LibraryModel) => {
    if (!lib.model_id) return
    try {
      const detail = await getModelLibraryDetail(lib.model_id)
      setDetailModel(detail)
      setDetailOpen(true)
    } catch {
      setDetailModel(lib)
      setDetailOpen(true)
    }
  }

  const openConfigDrawer = useCallback(
    (model: Model) => {
      setEditingModel(model)
      setValidation(null)
      form.setFieldsValue(paramsCfgToForm(model))
      setConfigOpen(true)
    },
    [form]
  )

  const projectColumns: ColumnsType<Model> = useMemo(
    () => [
      { title: '名称', dataIndex: 'name', key: 'name' },
      { title: '架构', dataIndex: 'arch_type', key: 'arch_type', render: (v) => <Tag>{v}</Tag> },
      {
        title: '预训练',
        dataIndex: 'pretrained',
        key: 'pretrained',
        render: (v: boolean) => (v ? <Tag color="green">是</Tag> : <Tag>否</Tag>),
      },
      {
        title: '更新时间',
        dataIndex: 'updated_at',
        key: 'updated_at',
        render: (v?: string) => (v ? new Date(v).toLocaleString() : '-'),
      },
      {
        title: '操作',
        key: 'action',
        render: (_, record) => (
          <Button type="link" icon={<SettingOutlined />} onClick={() => openConfigDrawer(record)}>
            参数配置
          </Button>
        ),
      },
    ],
    [openConfigDrawer]
  )

  const libraryContent = (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Space wrap>
        <Select
          style={{ width: 160 }}
          value={taskFilter}
          options={TASK_TYPE_OPTIONS}
          onChange={(v) => setTaskFilter(v as TaskType | '')}
        />
        <Input
          allowClear
          prefix={<SearchOutlined />}
          placeholder="搜索模型名称或架构"
          style={{ width: 280 }}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </Space>

      {libraryQuery.isLoading ? (
        <div style={{ textAlign: 'center', padding: 48 }}>
          <Spin />
        </div>
      ) : (libraryQuery.data?.length ?? 0) === 0 ? (
        <Empty description="暂无匹配的预置模型" />
      ) : (
        <Row gutter={[16, 16]}>
          {(libraryQuery.data ?? []).map((lib) => (
            <Col key={lib.model_id} xs={24} sm={12} lg={8}>
              <Card
                hoverable
                title={lib.name}
                extra={<Tag>{lib.task_type}</Tag>}
                actions={[
                  <Button key="detail" type="link" onClick={() => void openLibraryDetail(lib)}>
                    详情
                  </Button>,
                  <Button
                    key="adopt"
                    type="link"
                    icon={<PlusOutlined />}
                    loading={adoptMutation.isPending}
                    onClick={() => adoptMutation.mutate(lib)}
                  >
                    一键选用
                  </Button>,
                ]}
              >
                <Paragraph type="secondary" ellipsis={{ rows: 2 }}>
                  {lib.description}
                </Paragraph>
                <Space wrap size={[4, 8]}>
                  <Tag color="blue">{lib.arch_type}</Tag>
                  <Text type="secondary">参数量 {formatParams(lib.num_params)}</Text>
                  {lib.pretrained_available && <Tag color="green">预训练</Tag>}
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </Space>
  )

  const myModelsContent = (
    <Card>
      {projectModelsQuery.isLoading ? (
        <Spin />
      ) : (
        <Table
          rowKey="id"
          columns={projectColumns}
          dataSource={projectModelsQuery.data?.items ?? []}
          pagination={false}
          locale={{ emptyText: '暂无项目模型，请从预置模型库一键选用' }}
        />
      )}
    </Card>
  )

  return (
    <div>
      <Space style={{ marginBottom: 24, width: '100%', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>模型构建</h2>
        <Link to={`/projects/${projectId}/training`}>前往训练监控（Day2）</Link>
      </Space>

      <Tabs
        items={[
          { key: 'library', label: '预置模型库', children: libraryContent },
          { key: 'mine', label: '我的模型', children: myModelsContent },
        ]}
      />

      <Drawer
        title={detailModel?.name ?? '模型详情'}
        width={520}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
      >
        {detailModel && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="架构">{detailModel.arch_type}</Descriptions.Item>
            <Descriptions.Item label="任务类型">{detailModel.task_type}</Descriptions.Item>
            <Descriptions.Item label="输入形状">
              {detailModel.input_shape?.join(' × ')}
            </Descriptions.Item>
            <Descriptions.Item label="参数量">{formatParams(detailModel.num_params)}</Descriptions.Item>
            <Descriptions.Item label="支持数据">
              {detailModel.supported_datasets?.join(', ')}
            </Descriptions.Item>
            <Descriptions.Item label="预训练">
              {detailModel.pretrained_available ? '可用' : '不可用'}
            </Descriptions.Item>
            <Descriptions.Item label="描述">{detailModel.description}</Descriptions.Item>
            <Descriptions.Item label="默认超参">
              <pre style={{ margin: 0, fontSize: 12 }}>
                {JSON.stringify(detailModel.default_hyperparams, null, 2)}
              </pre>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>

      <Drawer
        title={editingModel ? `参数配置 — ${editingModel.name}` : '参数配置'}
        width={560}
        open={configOpen}
        onClose={() => {
          setConfigOpen(false)
          setEditingModel(null)
          setValidation(null)
        }}
        extra={
          <Space>
            <Button onClick={() => validateMutation.mutate(form.getFieldsValue())} loading={validateMutation.isPending}>
              校验配置
            </Button>
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              loading={saveMutation.isPending}
              onClick={() => form.submit()}
            >
              保存配置
            </Button>
          </Space>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => saveMutation.mutate(values)}
        >
          <Form.Item name="name" label="模型名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>

          {isImageArch(editingModel?.arch_type) ? (
            <>
              <Form.Item name="num_classes" label="类别数" rules={[{ required: true }]}>
                <InputNumber min={2} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="image_size" label="输入尺寸" rules={[{ required: true }]}>
                <InputNumber min={32} style={{ width: '100%' }} />
              </Form.Item>
            </>
          ) : (
            <>
              <Form.Item name="hidden_dims" label="隐藏层维度（逗号分隔）" rules={[{ required: true }]}>
                <Input placeholder="128, 64" />
              </Form.Item>
              <Form.Item name="output_dim" label="输出维度" rules={[{ required: true }]}>
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </>
          )}

          <Form.Item name="learning_rate" label="学习率" rules={[{ required: true }]}>
            <InputNumber min={0.000001} step={0.0001} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="optimizer" label="优化器" rules={[{ required: true }]}>
            <Select options={OPTIMIZER_OPTIONS} />
          </Form.Item>
          <Form.Item name="loss_function" label="损失函数" rules={[{ required: true }]}>
            <Select options={LOSS_OPTIONS} />
          </Form.Item>
          <Form.Item name="batch_size" label="Batch Size" rules={[{ required: true }]}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="epochs" label="训练轮数" rules={[{ required: true }]}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="weight_decay" label="Weight Decay">
            <InputNumber min={0} step={0.0001} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="device" label="设备" rules={[{ required: true }]}>
            <Select options={DEVICE_OPTIONS} />
          </Form.Item>
        </Form>

        {validation && (
          <Alert
            style={{ marginTop: 16 }}
            type={validation.valid ? 'success' : 'warning'}
            showIcon
            message={validation.valid ? '校验通过' : '校验未通过'}
            description={
              <Space direction="vertical" size={4}>
                {(validation.errors ?? []).map((e) => (
                  <Text key={`e-${e.field}`} type="danger">
                    {e.field}: {e.message}
                  </Text>
                ))}
                {(validation.warnings ?? []).map((w) => (
                  <Text key={`w-${w.field}`} type="secondary">
                    {w.field}: {w.message}
                  </Text>
                ))}
              </Space>
            }
          />
        )}
      </Drawer>
    </div>
  )
}
