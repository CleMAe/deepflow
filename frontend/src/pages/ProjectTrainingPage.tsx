import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react'
const ReactECharts = lazy(() => import('echarts-for-react'))
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import {
  Button,
  Card,
  Checkbox,
  Col,
  Descriptions,
  Empty,
  Form,
  Input,
  InputNumber,
  Progress,
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
import type { ColumnsType } from 'antd/es/table'
import axios from 'axios'
import { listInferenceDatasets } from '@/api/inference'
import { listProjectModels } from '@/api/models'
import {
  createTrainingJob,
  getTrainingJob,
  listCheckpoints,
  listTrainingJobs,
  pauseTrainingJob,
  resumeTrainingJob,
  startTrainingJob,
  stopTrainingJob,
  type TrainingJob,
  type TrainingJobCreate,
  type TrainingStatus,
} from '@/api/training'
import { useTrainingMetricsMock } from '@/hooks/useTrainingMetricsMock'

const { Text } = Typography

const STATUS_COLORS: Record<TrainingStatus, string> = {
  pending: 'default',
  running: 'processing',
  paused: 'warning',
  success: 'success',
  failed: 'error',
  cancelled: 'default',
}

const STATUS_LABELS: Record<TrainingStatus, string> = {
  pending: '待启动',
  running: '训练中',
  paused: '已暂停',
  success: '已完成',
  failed: '失败',
  cancelled: '已终止',
}

const DEVICE_OPTIONS = [
  { label: '自动', value: 'auto' },
  { label: 'CPU', value: 'cpu' },
  { label: 'CUDA', value: 'cuda' },
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

interface CreateFormValues {
  name: string
  model_id: string
  dataset_id: string
  val_dataset_id?: string
  epochs: number
  batch_size: number
  learning_rate: number
  optimizer: string
  loss_function: string
  weight_decay: number
  device: string
  start_after_create?: boolean
}

function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { message?: string } | undefined
    if (data?.message) return data.message
  }
  if (error instanceof Error) return error.message
  return '操作失败'
}

function buildHyperparams(values: CreateFormValues) {
  return {
    epochs: values.epochs,
    batch_size: values.batch_size,
    learning_rate: values.learning_rate,
    optimizer: values.optimizer,
    loss_function: values.loss_function,
    weight_decay: values.weight_decay,
    lr_scheduler: 'none',
    grad_accum_steps: 1,
    mixed_precision: false,
    checkpoint_every_n_epochs: 1,
  } as TrainingJobCreate['hyperparams']
}

function defaultCreateValues(modelId?: string | null): Partial<CreateFormValues> {
  return {
    name: '',
    model_id: modelId ?? undefined,
    epochs: 10,
    batch_size: 32,
    learning_rate: 0.001,
    optimizer: 'adam',
    loss_function: 'cross_entropy',
    weight_decay: 0,
    device: 'auto',
    start_after_create: false,
  }
}

export default function ProjectTrainingPage() {
  const { projectId = '' } = useParams()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const [form] = Form.useForm<CreateFormValues>()
  const modelIdFromUrl = searchParams.get('modelId')
  const [activeTab, setActiveTab] = useState(() => (modelIdFromUrl ? 'create' : 'jobs'))
  const [monitorJobId, setMonitorJobId] = useState<string | null>(null)

  const jobsQuery = useQuery({
    queryKey: ['training-jobs', projectId],
    queryFn: () => listTrainingJobs(projectId),
    enabled: !!projectId,
    refetchInterval: activeTab === 'jobs' ? 5000 : false,
  })

  const modelsQuery = useQuery({
    queryKey: ['project-models', projectId],
    queryFn: () => listProjectModels(projectId),
    enabled: !!projectId,
  })

  const datasetsQuery = useQuery({
    queryKey: ['datasets', projectId],
    queryFn: () => listInferenceDatasets(projectId),
    enabled: !!projectId,
  })

  const monitorJobQuery = useQuery({
    queryKey: ['training-job', projectId, monitorJobId],
    queryFn: () => getTrainingJob(projectId, monitorJobId!),
    enabled: !!projectId && !!monitorJobId,
    refetchInterval: activeTab === 'monitor' ? 3000 : false,
  })

  const checkpointsQuery = useQuery({
    queryKey: ['training-checkpoints', projectId, monitorJobId],
    queryFn: () => listCheckpoints(projectId, monitorJobId!),
    enabled: !!projectId && !!monitorJobId && activeTab === 'monitor',
  })

  const monitorJob = monitorJobQuery.data ?? null
  const wsEnabled = activeTab === 'monitor' && monitorJob?.status === 'running'
  const { history, logs, latest } = useTrainingMetricsMock(monitorJob, wsEnabled)

  const readyDatasets = useMemo(
    () => (datasetsQuery.data?.items ?? []).filter((d) => d.status === 'ready' || !d.status),
    [datasetsQuery.data]
  )

  const modelOptions = useMemo(
    () =>
      (modelsQuery.data?.items ?? []).map((m) => ({
        label: `${m.name} (${m.arch_type})`,
        value: m.id!,
      })),
    [modelsQuery.data]
  )

  const datasetOptions = useMemo(
    () => readyDatasets.map((d) => ({ label: `${d.name} (${d.format})`, value: d.id! })),
    [readyDatasets]
  )

  useEffect(() => {
    if (modelIdFromUrl) {
      form.setFieldsValue(defaultCreateValues(modelIdFromUrl))
    }
  }, [modelIdFromUrl, form])

  const invalidateJobs = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: ['training-jobs', projectId] })
    if (monitorJobId) {
      void queryClient.invalidateQueries({ queryKey: ['training-job', projectId, monitorJobId] })
    }
  }, [queryClient, projectId, monitorJobId])

  const actionMutation = useMutation({
    mutationFn: async ({
      jobId,
      action,
    }: {
      jobId: string
      action: 'start' | 'pause' | 'resume' | 'stop'
    }) => {
      const fn = {
        start: startTrainingJob,
        pause: pauseTrainingJob,
        resume: resumeTrainingJob,
        stop: stopTrainingJob,
      }[action]
      return fn(projectId, jobId)
    },
    onSuccess: () => {
      message.success('操作成功')
      invalidateJobs()
    },
    onError: (error) => message.error(getErrorMessage(error)),
  })

  const createMutation = useMutation({
    mutationFn: async (values: CreateFormValues) => {
      const payload: TrainingJobCreate = {
        name: values.name,
        model_id: values.model_id,
        dataset_id: values.dataset_id,
        val_dataset_id: values.val_dataset_id,
        hyperparams: buildHyperparams(values),
        device: values.device as TrainingJobCreate['device'],
      }
      const job = await createTrainingJob(projectId, payload)
      if (values.start_after_create && job.id) {
        return startTrainingJob(projectId, job.id)
      }
      return job
    },
    onSuccess: (job) => {
      message.success('训练任务已创建')
      invalidateJobs()
      setActiveTab('jobs')
      if (job.id) {
        setMonitorJobId(job.id)
      }
    },
    onError: (error) => message.error(getErrorMessage(error)),
  })

  const openMonitor = (job: TrainingJob) => {
    setMonitorJobId(job.id ?? null)
    setActiveTab('monitor')
  }

  const onModelChange = (modelId: string) => {
    const model = modelsQuery.data?.items?.find((m) => m.id === modelId)
    const cfg = (model?.params_cfg ?? {}) as Record<string, unknown>
    form.setFieldsValue({
      learning_rate: typeof cfg.learning_rate === 'number' ? cfg.learning_rate : 0.001,
      batch_size: typeof cfg.batch_size === 'number' ? cfg.batch_size : 32,
      epochs: typeof cfg.epochs === 'number' ? cfg.epochs : 10,
      optimizer: typeof cfg.optimizer === 'string' ? cfg.optimizer : 'adam',
      loss_function: typeof cfg.loss_function === 'string' ? cfg.loss_function : 'cross_entropy',
      weight_decay: typeof cfg.weight_decay === 'number' ? cfg.weight_decay : 0,
      device: typeof cfg.device === 'string' ? cfg.device : 'auto',
    })
  }

  const lossChartOption = useMemo(() => {
    const steps = history.map((p) => p.step)
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['train_loss', 'val_loss', 'accuracy'] },
      xAxis: { type: 'category', data: steps },
      yAxis: [{ type: 'value', name: 'loss' }, { type: 'value', name: 'acc', max: 1 }],
      series: [
        { name: 'train_loss', type: 'line', data: history.map((p) => p.train_loss), smooth: true },
        { name: 'val_loss', type: 'line', data: history.map((p) => p.val_loss), smooth: true },
        {
          name: 'accuracy',
          type: 'line',
          yAxisIndex: 1,
          data: history.map((p) => p.accuracy),
          smooth: true,
        },
      ],
    }
  }, [history])

  const resourceChartOption = useMemo(() => {
    if (!latest) return {}
    return {
      series: [
        {
          type: 'gauge',
          name: 'GPU',
          min: 0,
          max: 100,
          data: [{ value: latest.gpu_util, name: 'GPU %' }],
        },
        {
          type: 'gauge',
          name: 'CPU',
          min: 0,
          max: 100,
          center: ['50%', '55%'],
          data: [{ value: latest.cpu_util, name: 'CPU %' }],
        },
        {
          type: 'gauge',
          name: 'Memory',
          min: 0,
          max: 100,
          center: ['80%', '55%'],
          data: [{ value: latest.memory_util, name: 'Mem %' }],
        },
      ],
    }
  }, [latest])

  const renderActions = (job: TrainingJob) => {
    const id = job.id!
    const status = job.status as TrainingStatus
    const loading = actionMutation.isPending
    const run = (action: 'start' | 'pause' | 'resume' | 'stop') =>
      actionMutation.mutate({ jobId: id, action })

    return (
      <Space wrap size="small">
        {status === 'pending' && (
          <Button size="small" type="primary" loading={loading} onClick={() => run('start')}>
            启动
          </Button>
        )}
        {status === 'running' && (
          <>
            <Button size="small" loading={loading} onClick={() => run('pause')}>
              暂停
            </Button>
            <Button size="small" danger loading={loading} onClick={() => run('stop')}>
              终止
            </Button>
          </>
        )}
        {status === 'paused' && (
          <>
            <Button size="small" type="primary" loading={loading} onClick={() => run('resume')}>
              恢复
            </Button>
            <Button size="small" danger loading={loading} onClick={() => run('stop')}>
              终止
            </Button>
          </>
        )}
        <Button size="small" onClick={() => openMonitor(job)}>
          监控
        </Button>
      </Space>
    )
  }

  const jobColumns: ColumnsType<TrainingJob> = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '模型', dataIndex: 'model_id', key: 'model_id', ellipsis: true },
    { title: '数据集', dataIndex: 'dataset_id', key: 'dataset_id', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: TrainingStatus) => (
        <Tag color={STATUS_COLORS[status]}>{STATUS_LABELS[status] ?? status}</Tag>
      ),
    },
    {
      title: '进度',
      key: 'progress',
      render: (_, record) => {
        const current = record.current_epoch ?? 0
        const total = record.total_epochs ?? record.hyperparams?.epochs ?? 0
        const percent = total ? Math.round((current / Number(total)) * 100) : 0
        return <Progress percent={percent} size="small" format={() => `${current}/${total}`} />
      },
    },
    { title: '设备', dataIndex: 'device', key: 'device', width: 80 },
    {
      title: '操作',
      key: 'action',
      width: 220,
      render: (_, record) => renderActions(record),
    },
  ]

  const jobsTab = (
    <Card>
      {jobsQuery.isLoading ? (
        <Spin />
      ) : (
        <Table
          rowKey="id"
          columns={jobColumns}
          dataSource={jobsQuery.data?.items ?? []}
          pagination={false}
          locale={{ emptyText: '暂无训练任务，请创建新任务' }}
        />
      )}
    </Card>
  )

  const createTab = (
    <Card title="创建训练任务">
      <Form
        form={form}
        layout="vertical"
        initialValues={defaultCreateValues(modelIdFromUrl)}
        onFinish={(values) => createMutation.mutate(values)}
      >
        <Form.Item name="name" label="任务名称" rules={[{ required: true, message: '请输入任务名称' }]}>
          <Input placeholder="例如：ResNet-18 第一轮训练" />
        </Form.Item>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="model_id" label="模型" rules={[{ required: true }]}>
              <Select options={modelOptions} placeholder="选择项目模型" onChange={onModelChange} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="dataset_id" label="训练数据集" rules={[{ required: true }]}>
              <Select options={datasetOptions} placeholder="选择 ready 数据集" />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="val_dataset_id" label="验证数据集（可选）">
          <Select allowClear options={datasetOptions} placeholder="默认同训练集" />
        </Form.Item>
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="epochs" label="Epochs" rules={[{ required: true }]}>
              <InputNumber min={1} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="batch_size" label="Batch Size" rules={[{ required: true }]}>
              <InputNumber min={1} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="learning_rate" label="学习率" rules={[{ required: true }]}>
              <InputNumber min={0.000001} step={0.0001} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="optimizer" label="优化器" rules={[{ required: true }]}>
              <Select options={OPTIMIZER_OPTIONS} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="loss_function" label="损失函数" rules={[{ required: true }]}>
              <Select options={LOSS_OPTIONS} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="device" label="设备" rules={[{ required: true }]}>
              <Select options={DEVICE_OPTIONS} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="weight_decay" label="Weight Decay">
          <InputNumber min={0} step={0.0001} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="start_after_create" valuePropName="checked">
          <Checkbox>创建后立即启动</Checkbox>
        </Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" loading={createMutation.isPending}>
            创建任务
          </Button>
          <Button onClick={() => form.resetFields()}>重置</Button>
        </Space>
      </Form>
      {modelOptions.length === 0 && (
        <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
          请先在{' '}
          <Link to={`/projects/${projectId}/models`}>模型构建</Link> 中添加模型配置。
        </Text>
      )}
    </Card>
  )

  const monitorTab = !monitorJobId ? (
    <Empty description="请从任务列表点击「监控」查看实时指标" />
  ) : monitorJobQuery.isLoading ? (
    <Spin />
  ) : !monitorJob ? (
    <Empty description="任务不存在" />
  ) : (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card size="small">
        <Descriptions column={3} size="small">
          <Descriptions.Item label="任务">{monitorJob.name}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={STATUS_COLORS[monitorJob.status as TrainingStatus]}>
              {STATUS_LABELS[monitorJob.status as TrainingStatus]}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="设备">{monitorJob.device}</Descriptions.Item>
          <Descriptions.Item label="Epoch">
            {monitorJob.current_epoch}/{monitorJob.total_epochs}
          </Descriptions.Item>
          {latest && (
            <>
              <Descriptions.Item label="吞吐">{latest.throughput}</Descriptions.Item>
              <Descriptions.Item label="ETA">{latest.eta}</Descriptions.Item>
            </>
          )}
        </Descriptions>
        <div style={{ marginTop: 12 }}>{renderActions(monitorJob)}</div>
      </Card>

      {monitorJob.status === 'running' ? (
        <>
          <Card title="训练曲线（Mock WebSocket）">
            <Suspense fallback={<Spin />}>
              {history.length > 0 ? (
                <ReactECharts option={lossChartOption} style={{ height: 320 }} />
              ) : (
                <Text type="secondary">等待指标推送…</Text>
              )}
            </Suspense>
          </Card>
          <Card title="资源监控">
            <Suspense fallback={<Spin />}>
              {latest && <ReactECharts option={resourceChartOption} style={{ height: 220 }} />}
            </Suspense>
          </Card>
        </>
      ) : (
        <Card>
          <Text type="secondary">
            任务未在运行中。启动任务后可查看 Mock WebSocket 实时曲线（Day3 切换真实 WS）。
          </Text>
        </Card>
      )}

      <Row gutter={16}>
        <Col span={12}>
          <Card title="训练日志" size="small">
            <div
              style={{
                maxHeight: 240,
                overflow: 'auto',
                fontFamily: 'monospace',
                fontSize: 12,
                background: '#fafafa',
                padding: 12,
              }}
            >
              {(logs.length > 0 ? logs : ['暂无日志']).map((line, i) => (
                <div key={`${line}-${i}`}>{line}</div>
              ))}
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Checkpoints" size="small">
            <Table
              size="small"
              rowKey="epoch"
              pagination={false}
              loading={checkpointsQuery.isLoading}
              dataSource={checkpointsQuery.data?.checkpoints ?? []}
              columns={[
                { title: 'Epoch', dataIndex: 'epoch', width: 70 },
                {
                  title: 'Best',
                  dataIndex: 'is_best',
                  width: 60,
                  render: (v: boolean) => (v ? <Tag color="green">是</Tag> : '-'),
                },
                {
                  title: 'val_loss',
                  key: 'val_loss',
                  render: (_, r) => r.metrics?.val_loss ?? '-',
                },
                { title: '路径', dataIndex: 'path', ellipsis: true },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </Space>
  )

  return (
    <div>
      <Space style={{ marginBottom: 24, width: '100%', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>训练监控</h2>
        <Link to={`/projects/${projectId}/models`}>模型构建</Link>
      </Space>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'jobs', label: '训练任务', children: jobsTab },
          { key: 'create', label: '创建任务', children: createTab },
          { key: 'monitor', label: '实时监控', children: monitorTab },
        ]}
      />
    </div>
  )
}