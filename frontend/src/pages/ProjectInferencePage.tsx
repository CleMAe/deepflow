import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Descriptions,
  Empty,
  Form,
  Input,
  Progress,
  Row,
  Select,
  Space,
  Statistic,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  evaluateModel,
  listInferenceDatasets,
  listInferenceModels,
  runOnlineInference,
  type Dataset,
  type EvaluateResult,
  type Model,
  type OnlineInferenceResult,
} from '@/api/inference'

const { Text } = Typography
const DEFAULT_METRICS = ['accuracy', 'precision', 'recall', 'f1']
const DEFAULT_ONLINE_INPUT = JSON.stringify(
  {
    age: 32,
    monthly_spend: 1260,
    visits_30d: 18,
    category: 'premium',
  },
  null,
  2
)

interface EvaluationFormValues {
  model_id: string
  dataset_id: string
  metrics: string[]
}

interface OnlineFormValues {
  model_id: string
  input_data: string
}

function formatPercent(value?: number) {
  if (typeof value !== 'number') {
    return '-'
  }
  return `${(value * 100).toFixed(1)}%`
}

function stringifyValue(value: unknown) {
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  return JSON.stringify(value)
}

function buildConfusionMatrixOption(result?: EvaluateResult) {
  const matrix = result?.confusion_matrix ?? []
  const labels = matrix.map((_, index) => `Class ${index + 1}`)
  const values = matrix.flatMap((row, y) => row.map((value, x) => [x, y, value]))
  const maxValue = Math.max(...matrix.flat(), 1)

  return {
    tooltip: {
      position: 'top',
      formatter: (params: { value: [number, number, number] }) => {
        const [x, y, value] = params.value
        return `${labels[y]} → ${labels[x]}: ${value}`
      },
    },
    grid: { top: 32, right: 24, bottom: 48, left: 72 },
    xAxis: {
      type: 'category',
      data: labels,
      splitArea: { show: true },
    },
    yAxis: {
      type: 'category',
      data: labels,
      splitArea: { show: true },
    },
    visualMap: {
      min: 0,
      max: maxValue,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: {
        color: ['#f6ffed', '#95de64', '#237804'],
      },
    },
    series: [
      {
        name: 'confusion_matrix',
        type: 'heatmap',
        data: values,
        label: { show: true },
        emphasis: {
          itemStyle: {
            shadowBlur: 8,
            shadowColor: 'rgba(0, 0, 0, 0.24)',
          },
        },
      },
    ],
  }
}

function modelLabel(model: Model) {
  return `${model.name ?? model.id} · ${model.arch_type ?? 'custom'}`
}

function datasetLabel(dataset: Dataset) {
  const samples = typeof dataset.num_samples === 'number' ? `${dataset.num_samples} samples` : 'samples pending'
  return `${dataset.name ?? dataset.id} · ${dataset.format ?? 'dataset'} · ${samples}`
}

function MetricCards({ result }: { result?: EvaluateResult }) {
  const metrics = result?.metrics ?? {}

  return (
    <Row gutter={[16, 16]}>
      {DEFAULT_METRICS.map((key) => (
        <Col xs={12} lg={6} key={key}>
          <Card size="small">
            <Statistic title={key.toUpperCase()} value={formatPercent(metrics[key])} />
          </Card>
        </Col>
      ))}
      <Col xs={12} lg={6}>
        <Card size="small">
          <Statistic title="SAMPLES" value={result?.num_samples ?? '-'} />
        </Card>
      </Col>
    </Row>
  )
}

function OnlineResult({ result }: { result?: OnlineInferenceResult }) {
  const probabilities = Object.entries(result?.probabilities ?? {})

  if (!result) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无推理结果" />
  }

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Descriptions bordered size="small" column={1}>
        <Descriptions.Item label="预测结果">{stringifyValue(result.prediction)}</Descriptions.Item>
        <Descriptions.Item label="置信度">{formatPercent(result.confidence)}</Descriptions.Item>
        <Descriptions.Item label="延迟">{typeof result.latency_ms === 'number' ? `${result.latency_ms} ms` : '-'}</Descriptions.Item>
      </Descriptions>
      <Space direction="vertical" size={10} style={{ width: '100%' }}>
        {probabilities.map(([label, value]) => (
          <div key={label}>
            <Space style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <Text>{label}</Text>
              <Text type="secondary">{formatPercent(value)}</Text>
            </Space>
            <Progress percent={Number((value * 100).toFixed(1))} showInfo={false} />
          </div>
        ))}
      </Space>
    </Space>
  )
}

export default function ProjectInferencePage() {
  const { projectId } = useParams()
  const [messageApi, contextHolder] = message.useMessage()
  const [evaluationResult, setEvaluationResult] = useState<EvaluateResult>()
  const [onlineResult, setOnlineResult] = useState<OnlineInferenceResult>()

  const modelsQuery = useQuery({
    queryKey: ['p5-models', projectId],
    queryFn: () => listInferenceModels(projectId!),
    enabled: !!projectId,
  })

  const datasetsQuery = useQuery({
    queryKey: ['p5-datasets', projectId],
    queryFn: () => listInferenceDatasets(projectId!),
    enabled: !!projectId,
  })

  const modelOptions = useMemo(
    () =>
      (modelsQuery.data?.items ?? []).map((model) => ({
        label: modelLabel(model),
        value: model.id,
      })),
    [modelsQuery.data?.items]
  )

  const datasetOptions = useMemo(
    () =>
      (datasetsQuery.data?.items ?? []).map((dataset) => ({
        label: datasetLabel(dataset),
        value: dataset.id,
      })),
    [datasetsQuery.data?.items]
  )

  const evaluateMutation = useMutation({
    mutationFn: (values: EvaluationFormValues) =>
      evaluateModel(projectId!, {
        model_id: values.model_id,
        dataset_id: values.dataset_id,
        metrics: values.metrics,
      }),
    onSuccess: (data) => {
      setEvaluationResult(data)
      messageApi.success('模型评估完成')
    },
    onError: () => {
      messageApi.error('模型评估失败')
    },
  })

  const onlineMutation = useMutation({
    mutationFn: (values: OnlineFormValues) => {
      let inputData: Record<string, unknown> | string
      try {
        const parsed = JSON.parse(values.input_data) as unknown
        if (typeof parsed !== 'string' && (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed))) {
          throw new Error('invalid shape')
        }
        inputData = typeof parsed === 'string' ? parsed : (parsed as Record<string, unknown>)
      } catch {
        messageApi.error('输入必须是 JSON 对象或 JSON 字符串')
        return Promise.reject(new Error('invalid json'))
      }

      return runOnlineInference(projectId!, {
        model_id: values.model_id,
        input_data: inputData,
      })
    },
    onSuccess: (data) => {
      setOnlineResult(data)
      messageApi.success('在线测试完成')
    },
    onError: (error) => {
      if (error instanceof Error && error.message === 'invalid json') {
        return
      }
      messageApi.error('在线测试失败')
    },
  })

  const loadingOptions = modelsQuery.isLoading || datasetsQuery.isLoading

  const evaluationPanel = (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card>
        <Form<EvaluationFormValues>
          layout="vertical"
          initialValues={{ metrics: DEFAULT_METRICS }}
          onFinish={(values) => evaluateMutation.mutate(values)}
        >
          <Row gutter={16}>
            <Col xs={24} lg={10}>
              <Form.Item name="model_id" label="模型" rules={[{ required: true, message: '请选择模型' }]}>
                <Select loading={modelsQuery.isLoading} options={modelOptions} placeholder="选择模型" />
              </Form.Item>
            </Col>
            <Col xs={24} lg={10}>
              <Form.Item name="dataset_id" label="数据集" rules={[{ required: true, message: '请选择数据集' }]}>
                <Select loading={datasetsQuery.isLoading} options={datasetOptions} placeholder="选择数据集" />
              </Form.Item>
            </Col>
            <Col xs={24} lg={4}>
              <Form.Item label=" " colon={false}>
                <Button type="primary" htmlType="submit" block loading={evaluateMutation.isPending} disabled={loadingOptions}>
                  开始评估
                </Button>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="metrics" label="指标">
            <Checkbox.Group
              options={[
                { label: 'Accuracy', value: 'accuracy' },
                { label: 'Precision', value: 'precision' },
                { label: 'Recall', value: 'recall' },
                { label: 'F1', value: 'f1' },
              ]}
            />
          </Form.Item>
        </Form>
      </Card>

      {evaluationResult ? (
        <>
          <MetricCards result={evaluationResult} />
          <Card title="混淆矩阵">
            <ReactECharts option={buildConfusionMatrixOption(evaluationResult)} style={{ height: 360 }} />
          </Card>
        </>
      ) : (
        <Card>
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无评估结果" />
        </Card>
      )}
    </Space>
  )

  const onlinePanel = (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}>
        <Card>
          <Form<OnlineFormValues>
            layout="vertical"
            initialValues={{ input_data: DEFAULT_ONLINE_INPUT }}
            onFinish={(values) => onlineMutation.mutate(values)}
          >
            <Form.Item name="model_id" label="模型" rules={[{ required: true, message: '请选择模型' }]}>
              <Select loading={modelsQuery.isLoading} options={modelOptions} placeholder="选择模型" />
            </Form.Item>
            <Form.Item name="input_data" label="输入 JSON" rules={[{ required: true, message: '请输入 JSON' }]}>
              <Input.TextArea rows={12} spellCheck={false} />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={onlineMutation.isPending} disabled={modelsQuery.isLoading}>
              运行测试
            </Button>
          </Form>
        </Card>
      </Col>
      <Col xs={24} lg={12}>
        <Card
          title="推理结果"
          extra={
            onlineResult?.confidence ? (
              <Tag color={onlineResult.confidence >= 0.8 ? 'green' : 'orange'}>{formatPercent(onlineResult.confidence)}</Tag>
            ) : null
          }
        >
          <OnlineResult result={onlineResult} />
        </Card>
      </Col>
    </Row>
  )

  return (
    <div>
      {contextHolder}
      <h2 style={{ marginBottom: 24 }}>推理测试</h2>
      {!projectId && <Alert type="warning" showIcon message="未选择项目" style={{ marginBottom: 16 }} />}
      <Tabs
        items={[
          {
            key: 'evaluate',
            label: '模型评估',
            children: evaluationPanel,
          },
          {
            key: 'online',
            label: '在线测试',
            children: onlinePanel,
          },
        ]}
      />
    </div>
  )
}
