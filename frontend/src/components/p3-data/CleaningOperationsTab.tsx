import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  Row,
  Select,
  Space,
  Switch,
  Typography,
  message,
} from 'antd'
import { listDatasets, type Dataset } from '@/api/datasets'
import { datasetOptionLabel, isTabularDataset } from '@/components/p3-data/datasetFormat'
import { formatApiError } from '@/lib/formatApiError'
import {
  cleanDedup,
  cleanEncode,
  cleanMissing,
  cleanOutlier,
  cleanTypeConvert,
  type CleanDedupRequest,
  type CleanEncodeRequest,
  type CleanMissingRequest,
  type CleanOutlierRequest,
  type CleanTypeConvertRequest,
  type CleaningResult,
} from '@/api/cleaningEda'

const { Text } = Typography

interface CleaningOperationsTabProps {
  projectId: string
}

const MISSING_STRATEGIES: CleanMissingRequest['strategy'][] = [
  'drop_row',
  'fill_mean',
  'fill_median',
  'fill_mode',
  'fill_constant',
  'forward_fill',
  'backward_fill',
]

const OUTLIER_METHODS: CleanOutlierRequest['method'][] = ['zscore', 'iqr', 'isolation_forest']
const OUTLIER_ACTIONS: CleanOutlierRequest['action'][] = ['drop', 'clip', 'mark']
const DEDUP_KEEP: CleanDedupRequest['keep'][] = ['first', 'last', 'none']
const ENCODE_METHODS: CleanEncodeRequest['method'][] = [
  'label_encoding',
  'one_hot',
  'target_encoding',
  'frequency_encoding',
]

function ResultAlert({ result }: { result: CleaningResult | null }) {
  if (!result) return null
  return (
    <Alert
      type="success"
      showIcon
      style={{ marginTop: 16 }}
      message="执行结果"
      description={
        <Space direction="vertical" size={4}>
          <Text>
            行数：{result.rows_before ?? '-'} → {result.rows_after ?? '-'}
          </Text>
          {result.columns_affected?.length ? (
            <Text>涉及列：{result.columns_affected.join(', ')}</Text>
          ) : null}
        </Space>
      }
    />
  )
}

export default function CleaningOperationsTab({ projectId }: CleaningOperationsTabProps) {
  const queryClient = useQueryClient()
  const [datasetId, setDatasetId] = useState<string>()
  const [lastResult, setLastResult] = useState<CleaningResult | null>(null)

  const [missingForm] = Form.useForm<CleanMissingRequest>()
  const [outlierForm] = Form.useForm<CleanOutlierRequest>()
  const [dedupForm] = Form.useForm<CleanDedupRequest>()
  const [encodeForm] = Form.useForm<CleanEncodeRequest>()
  const [typeForm] = Form.useForm<CleanTypeConvertRequest>()

  const datasetsQuery = useQuery({
    queryKey: ['datasets', projectId, 'cleaning'],
    queryFn: () => listDatasets(projectId, { page: 1, page_size: 100 }),
    enabled: !!projectId,
  })

  const tabularItems = useMemo(
    () => (datasetsQuery.data?.items ?? []).filter((d: Dataset) => isTabularDataset(d)),
    [datasetsQuery.data?.items],
  )

  const options = useMemo(
    () =>
      tabularItems.map((d: Dataset) => ({
        value: d.id!,
        label: datasetOptionLabel(d),
      })),
    [tabularItems],
  )

  const invalidate = () => void queryClient.invalidateQueries({ queryKey: ['datasets', projectId] })

  const missingMut = useMutation({
    mutationFn: (body: CleanMissingRequest) => cleanMissing(projectId, datasetId!, body),
    onSuccess: (data) => {
      setLastResult(data)
      message.success('缺失值处理已提交')
      invalidate()
    },
    onError: (err) => message.error(formatApiError(err)),
  })

  const outlierMut = useMutation({
    mutationFn: (body: CleanOutlierRequest) => cleanOutlier(projectId, datasetId!, body),
    onSuccess: (data) => {
      setLastResult(data)
      message.success('异常值处理已提交')
      invalidate()
    },
    onError: (err) => message.error(formatApiError(err)),
  })

  const dedupMut = useMutation({
    mutationFn: (body: CleanDedupRequest) => cleanDedup(projectId, datasetId!, body),
    onSuccess: (data) => {
      setLastResult(data)
      message.success('去重已提交')
      invalidate()
    },
    onError: (err) => message.error(formatApiError(err)),
  })

  const encodeMut = useMutation({
    mutationFn: (body: CleanEncodeRequest) => cleanEncode(projectId, datasetId!, body),
    onSuccess: (data) => {
      setLastResult(data)
      message.success('编码转换已提交')
      invalidate()
    },
    onError: (err) => message.error(formatApiError(err)),
  })

  const typeMut = useMutation({
    mutationFn: (body: CleanTypeConvertRequest) => cleanTypeConvert(projectId, datasetId!, body),
    onSuccess: (data) => {
      setLastResult(data)
      message.success('类型转换已提交')
      invalidate()
    },
    onError: (err) => message.error(formatApiError(err)),
  })

  const requireDs = () => {
    if (!datasetId) {
      message.warning('请先选择数据集')
      return false
    }
    return true
  }

  if (datasetsQuery.isError) {
    return (
      <Alert
        type="error"
        showIcon
        message="无法加载数据集"
        description={formatApiError(datasetsQuery.error, '请从工作台进入 Demo Project')}
      />
    )
  }

  return (
    <div>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="仅支持 CSV / JSON 表格数据集"
        description="图像数据集请使用「数据增强」页；清洗结果会写回数据集文件。"
      />
      <Space wrap style={{ marginBottom: 16 }}>
        <Text>当前数据集：</Text>
        <Select
          allowClear
          showSearch
          optionFilterProp="label"
          placeholder="选择数据集"
          style={{ minWidth: 280 }}
          options={options}
          value={datasetId}
          onChange={(v) => setDatasetId(v)}
          loading={datasetsQuery.isLoading}
        />
      </Space>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="缺失值处理" size="small">
            <Form
              form={missingForm}
              layout="vertical"
              initialValues={{ strategy: 'fill_mean', create_new_version: true }}
              onFinish={(v) => {
                if (!requireDs()) return
                missingMut.mutate({
                  ...v,
                  columns: v.columns?.filter(Boolean),
                })
              }}
            >
              <Form.Item name="strategy" label="策略" rules={[{ required: true }]}>
                <Select options={MISSING_STRATEGIES.map((s) => ({ value: s, label: s }))} />
              </Form.Item>
              <Form.Item name="columns" label="目标列（留空表示自动检测）">
                <Select mode="tags" placeholder="例如 age, income" tokenSeparators={[',']} />
              </Form.Item>
              <Form.Item noStyle shouldUpdate={(p, c) => p.strategy !== c.strategy}>
                {() =>
                  missingForm.getFieldValue('strategy') === 'fill_constant' ? (
                    <Form.Item name="fill_value" label="填充常量">
                      <Input placeholder="常量值" />
                    </Form.Item>
                  ) : null
                }
              </Form.Item>
              <Form.Item name="create_new_version" label="生成新版本" valuePropName="checked">
                <Switch />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={missingMut.isPending}>
                执行
              </Button>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="异常值处理" size="small">
            <Form
              form={outlierForm}
              layout="vertical"
              initialValues={{ method: 'iqr', action: 'drop', threshold: 1.5 }}
              onFinish={(v) => {
                if (!requireDs()) return
                outlierMut.mutate(v)
              }}
            >
              <Form.Item name="columns" label="目标列" rules={[{ required: true, message: '至少一列' }]}>
                <Select mode="tags" placeholder="例如 sales, visits" tokenSeparators={[',']} />
              </Form.Item>
              <Form.Item name="method" label="方法" rules={[{ required: true }]}>
                <Select options={OUTLIER_METHODS.map((m) => ({ value: m, label: m }))} />
              </Form.Item>
              <Form.Item name="threshold" label="阈值（Z-score / IQR 倍数）">
                <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="action" label="处理方式" rules={[{ required: true }]}>
                <Select options={OUTLIER_ACTIONS.map((a) => ({ value: a, label: a }))} />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={outlierMut.isPending}>
                执行
              </Button>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="去重" size="small">
            <Form
              form={dedupForm}
              layout="vertical"
              initialValues={{ keep: 'first' }}
              onFinish={(v) => {
                if (!requireDs()) return
                dedupMut.mutate({
                  ...v,
                  columns: v.columns?.filter(Boolean),
                })
              }}
            >
              <Form.Item name="columns" label="判定列（留空为全列）">
                <Select mode="tags" placeholder="例如 order_id" tokenSeparators={[',']} />
              </Form.Item>
              <Form.Item name="keep" label="保留策略" rules={[{ required: true }]}>
                <Select options={DEDUP_KEEP.map((k) => ({ value: k, label: k }))} />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={dedupMut.isPending}>
                执行
              </Button>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="编码转换" size="small">
            <Form
              form={encodeForm}
              layout="vertical"
              initialValues={{ method: 'label_encoding' }}
              onFinish={(v) => {
                if (!requireDs()) return
                encodeMut.mutate(v)
              }}
            >
              <Form.Item name="columns" label="列" rules={[{ required: true }]}>
                <Select mode="tags" placeholder="例如 region" tokenSeparators={[',']} />
              </Form.Item>
              <Form.Item name="method" label="编码方式" rules={[{ required: true }]}>
                <Select options={ENCODE_METHODS.map((m) => ({ value: m, label: m }))} />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={encodeMut.isPending}>
                执行
              </Button>
            </Form>
          </Card>
        </Col>

        <Col span={24}>
          <Card title="类型转换" size="small">
            <Form
              form={typeForm}
              layout="vertical"
              initialValues={{
                conversions: [{ column: 'date', target_type: 'datetime', datetime_format: '%Y-%m-%d' }],
              }}
              onFinish={(v) => {
                if (!requireDs()) return
                typeMut.mutate(v)
              }}
            >
              <Form.List name="conversions">
                {(fields, { add, remove }) => (
                  <>
                    {fields.map((field) => (
                      <Space key={field.key} align="start" wrap style={{ marginBottom: 8 }}>
                        <Form.Item name={[field.name, 'column']} label="列名" rules={[{ required: true }]}>
                          <Input placeholder="column" />
                        </Form.Item>
                        <Form.Item name={[field.name, 'target_type']} label="目标类型" rules={[{ required: true }]}>
                          <Select
                            style={{ width: 160 }}
                            options={['int', 'float', 'str', 'bool', 'datetime'].map((t) => ({
                              value: t,
                              label: t,
                            }))}
                          />
                        </Form.Item>
                        <Form.Item name={[field.name, 'datetime_format']} label="日期格式（可选）">
                          <Input placeholder="%Y-%m-%d" style={{ width: 140 }} />
                        </Form.Item>
                        <Button danger type="link" onClick={() => remove(field.name)}>
                          删除
                        </Button>
                      </Space>
                    ))}
                    <Button type="dashed" onClick={() => add({ column: '', target_type: 'float' })} block>
                      添加一行
                    </Button>
                  </>
                )}
              </Form.List>
              <Button type="primary" htmlType="submit" loading={typeMut.isPending} style={{ marginTop: 12 }}>
                执行
              </Button>
            </Form>
          </Card>
        </Col>
      </Row>

      <ResultAlert result={lastResult} />
    </div>
  )
}
