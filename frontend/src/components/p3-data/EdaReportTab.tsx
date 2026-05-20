import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Button, Card, Descriptions, Empty, Select, Space, Table, Typography, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import { listDatasets, type Dataset } from '@/api/datasets'
import { getEdaReport, runEda, type EDAReport } from '@/api/cleaningEda'
import type { components } from '@/api/types'

type ColumnStat = components['schemas']['ColumnStat']
type Visualization = components['schemas']['Visualization']

const { Text } = Typography

interface EdaReportTabProps {
  projectId: string
}

function chartHeight(v: Visualization) {
  return v.type === 'heatmap' ? 360 : 280
}

function toOption(v: Visualization): EChartsOption | null {
  if (v.config && typeof v.config === 'object') {
    return v.config as EChartsOption
  }
  return null
}

export default function EdaReportTab({ projectId }: EdaReportTabProps) {
  const [datasetId, setDatasetId] = useState<string>()
  const [localReport, setLocalReport] = useState<EDAReport | null>(null)

  const datasetsQuery = useQuery({
    queryKey: ['datasets', projectId, 'eda'],
    queryFn: () => listDatasets(projectId, { page: 1, page_size: 100 }),
    enabled: !!projectId,
  })

  const reportQuery = useQuery({
    queryKey: ['eda-report', projectId, datasetId],
    queryFn: () => getEdaReport(projectId, datasetId!),
    enabled: !!projectId && !!datasetId,
  })

  const report = localReport ?? reportQuery.data ?? null

  const runMut = useMutation({
    mutationFn: () =>
      runEda(projectId, datasetId!, {
        include_visualizations: true,
      }),
    onSuccess: (data) => {
      setLocalReport(data)
      message.success('EDA 分析完成（Mock）')
      void reportQuery.refetch()
    },
    onError: () => message.error('EDA 触发失败'),
  })

  const statColumns: ColumnsType<ColumnStat> = [
    { title: '列名', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'dtype', key: 'dtype', width: 100 },
    { title: '缺失数', dataIndex: 'missing_count', key: 'missing_count', width: 90 },
    { title: '缺失%', dataIndex: 'missing_pct', key: 'missing_pct', width: 90 },
    { title: '唯一值', dataIndex: 'unique_count', key: 'unique_count', width: 90 },
    { title: '均值', dataIndex: 'mean', key: 'mean', width: 90 },
    { title: '中位数', dataIndex: 'median', key: 'median', width: 90 },
  ]

  const dsOptions = (datasetsQuery.data?.items ?? []).map((d: Dataset) => ({
    value: d.id!,
    label: `${d.name ?? d.id} (${d.format ?? '?'})`,
  }))

  return (
    <div>
      <Space wrap style={{ marginBottom: 16 }}>
        <Text>数据集：</Text>
        <Select
          allowClear
          showSearch
          optionFilterProp="label"
          placeholder="选择数据集"
          style={{ minWidth: 280 }}
          options={dsOptions}
          value={datasetId}
          onChange={(v) => {
            setDatasetId(v)
            setLocalReport(null)
          }}
          loading={datasetsQuery.isLoading}
        />
        <Button
          type="primary"
          disabled={!datasetId}
          loading={runMut.isPending}
          onClick={() => {
            if (!datasetId) return
            runMut.mutate()
          }}
        >
          运行 EDA
        </Button>
        <Button disabled={!datasetId} loading={reportQuery.isFetching} onClick={() => void reportQuery.refetch()}>
          刷新报告
        </Button>
      </Space>

      {!datasetId ? (
        <Empty description="请选择数据集后运行 EDA" />
      ) : reportQuery.isLoading && !localReport ? (
        <Text type="secondary">加载中…</Text>
      ) : !report ? (
        <Empty description="点击「运行 EDA」生成报告（Mock）" />
      ) : (
        <>
          <Card title="统计概览" size="small" style={{ marginBottom: 16 }}>
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="行数">{report.summary?.num_rows ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="列数">{report.summary?.num_columns ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="缺失单元">{report.summary?.num_missing ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="重复行">{report.summary?.duplicate_rows ?? '-'}</Descriptions.Item>
            </Descriptions>
          </Card>

          <Card title="列统计" size="small" style={{ marginBottom: 16 }}>
            <Table
              size="small"
              rowKey={(r) => r.name ?? String(Math.random())}
              columns={statColumns}
              dataSource={report.column_stats ?? []}
              pagination={false}
              scroll={{ x: true }}
            />
          </Card>

          <Typography.Title level={5}>可视化（ECharts · Mock 数据）</Typography.Title>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {(report.visualizations ?? []).map((viz, idx) => {
              const opt = toOption(viz)
              if (!opt) return null
              return (
                <Card key={`${viz.title}-${idx}`} title={viz.title} size="small">
                  <ReactECharts option={opt} style={{ height: chartHeight(viz), width: '100%' }} notMerge lazyUpdate />
                </Card>
              )
            })}
          </Space>
        </>
      )}
    </div>
  )
}
