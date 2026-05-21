import { lazy, Suspense, useMemo, useState } from 'react'
const ReactECharts = lazy(() => import('echarts-for-react'))
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button,
  Card,
  Drawer,
  Form,
  Input,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import axios from 'axios'
import {
  compareExperiments,
  listExperiments,
  updateExperiment,
  type Experiment,
} from '@/api/experiments'

const { Text } = Typography

function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { message?: string } | undefined
    if (data?.message) return data.message
  }
  if (error instanceof Error) return error.message
  return '操作失败'
}

interface EditFormValues {
  tags: string[]
  notes: string
}

export default function ExperimentsPanel({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient()
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [compareResult, setCompareResult] = useState<Awaited<ReturnType<typeof compareExperiments>> | null>(
    null
  )
  const [editing, setEditing] = useState<Experiment | null>(null)
  const [form] = Form.useForm<EditFormValues>()

  const listQuery = useQuery({
    queryKey: ['experiments', projectId],
    queryFn: () => listExperiments(projectId),
    enabled: !!projectId,
  })

  const compareMutation = useMutation({
    mutationFn: () => compareExperiments(projectId, selectedIds),
    onSuccess: (data) => {
      setCompareResult(data)
      message.success('对比完成')
    },
    onError: (error) => message.error(getErrorMessage(error)),
  })

  const updateMutation = useMutation({
    mutationFn: (values: EditFormValues) =>
      updateExperiment(projectId, editing!.id!, { tags: values.tags, notes: values.notes }),
    onSuccess: () => {
      message.success('已保存')
      setEditing(null)
      void queryClient.invalidateQueries({ queryKey: ['experiments', projectId] })
    },
    onError: (error) => message.error(getErrorMessage(error)),
  })

  const compareChartOption = useMemo(() => {
    const mc = compareResult?.metric_comparison ?? {}
    const keys = Object.keys(mc)
    if (!keys.length) return null
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: selectedIds },
      xAxis: { type: 'category', data: keys },
      series: selectedIds.map((id, index) => ({
        name: listQuery.data?.items?.find((e) => e.id === id)?.name ?? id,
        type: 'bar',
        data: keys.map((k) => mc[k]?.[index] ?? 0),
      })),
    }
  }, [compareResult, selectedIds, listQuery.data])

  const columns: ColumnsType<Experiment> = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '任务', dataIndex: 'job_id', key: 'job_id', ellipsis: true, width: 120 },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[] | undefined) =>
        (tags ?? []).map((t) => (
          <Tag key={t}>{t}</Tag>
        )),
    },
    {
      title: '指标',
      key: 'metrics',
      render: (_, r) => {
        const m = r.metrics as Record<string, number> | undefined
        if (!m) return '-'
        const top = Object.entries(m)
          .slice(0, 2)
          .map(([k, v]) => `${k}: ${typeof v === 'number' ? v.toFixed(3) : v}`)
        return top.join(', ')
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          onClick={() => {
            setEditing(record)
            form.setFieldsValue({
              tags: record.tags ?? [],
              notes: record.notes ?? '',
            })
          }}
        >
          编辑
        </Button>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space style={{ marginBottom: 16 }} wrap>
          <Text type="secondary">选择 2 个及以上实验进行对比</Text>
          <Select
            mode="multiple"
            style={{ minWidth: 320 }}
            placeholder="选择实验"
            value={selectedIds}
            onChange={setSelectedIds}
            options={(listQuery.data?.items ?? []).map((e) => ({
              label: e.name,
              value: e.id!,
            }))}
          />
          <Button
            type="primary"
            disabled={selectedIds.length < 2}
            loading={compareMutation.isPending}
            onClick={() => compareMutation.mutate()}
          >
            对比实验
          </Button>
        </Space>
        {listQuery.isLoading ? (
          <Spin />
        ) : (
          <Table
            rowKey="id"
            columns={columns}
            dataSource={listQuery.data?.items ?? []}
            pagination={false}
            locale={{ emptyText: '暂无实验记录，请先完成训练任务' }}
          />
        )}
      </Card>

      {compareResult && compareChartOption && (
        <Card title="指标对比">
          <Suspense fallback={<Spin />}>
            <ReactECharts option={compareChartOption} style={{ height: 320 }} />
          </Suspense>
        </Card>
      )}

      <Drawer
        title={editing ? `编辑实验 — ${editing.name}` : '编辑实验'}
        open={!!editing}
        onClose={() => setEditing(null)}
        width={480}
        extra={
          <Button type="primary" loading={updateMutation.isPending} onClick={() => form.submit()}>
            保存
          </Button>
        }
      >
        <Form form={form} layout="vertical" onFinish={(v) => updateMutation.mutate(v)}>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" placeholder="输入后回车添加标签" />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Drawer>
    </Space>
  )
}
