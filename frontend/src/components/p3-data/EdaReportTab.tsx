import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Alert, Button, Card, Empty, Select, Space, Table, Typography, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import ReactECharts from 'echarts-for-react'
import { listDatasets, type Dataset } from '@/api/datasets'
import { getEdaReport, runEda, type EDAReport } from '@/api/cleaningEda'
import { datasetOptionLabel, isTabularDataset } from '@/components/p3-data/datasetFormat'
import { mergeEChartsOption } from '@/lib/echartsDefaults'
import { formatApiError } from '@/lib/formatApiError'
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

export default function EdaReportTab({ projectId }: EdaReportTabProps) {
  const [datasetId, setDatasetId] = useState<string>()
  const [localReport, setLocalReport] = useState<EDAReport | null>(null)
  const [shouldFetchReport, setShouldFetchReport] = useState(false)

  const datasetsQuery = useQuery({
    queryKey: ['datasets', projectId, 'eda'],
    queryFn: () => listDatasets(projectId, { page: 1, page_size: 100 }),
    enabled: !!projectId,
  })

  const tabularItems = (datasetsQuery.data?.items ?? []).filter((d: Dataset) => isTabularDataset(d))

  const reportQuery = useQuery({
    queryKey: ['eda-report', projectId, datasetId],
    queryFn: () => getEdaReport(projectId, datasetId!),
    enabled: !!projectId && !!datasetId && shouldFetchReport,
    retry: false,
  })

  const report = localReport ?? reportQuery.data ?? null

  const runMut = useMutation({
    mutationFn: () =>
      runEda(projectId, datasetId!, {
        include_visualizations: true,
      }),
    onSuccess: (data) => {
      setLocalReport(data)
      setShouldFetchReport(true)
      message.success('EDA 分析完成')
    },
    onError: (err) => message.error(formatApiError(err, 'EDA 触发失败')),
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

  const dsOptions = tabularItems.map((d: Dataset) => ({
    value: d.id!,
    label: datasetOptionLabel(d),
  }))

  const reportError =
    reportQuery.isError && shouldFetchReport && !localReport
      ? formatApiError(reportQuery.error, '暂无报告')
      : null

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

  const mainContent = !datasetId ? (
    <Empty description="请在左侧选择表格数据集后运行 EDA" />
  ) : reportQuery.isLoading && shouldFetchReport && !localReport ? (
    <Text type="secondary">加载中…</Text>
  ) : reportError && !report ? (
    <Empty description={reportError} />
  ) : !report ? (
    <Empty description="点击「运行 EDA」生成统计报告与图表" />
  ) : (
    <>
      <div className="p3-ds-stats">
        <div className="p3-ds-stat-card">
          <span className="label">行数</span>
          <span className="value">{report.summary?.num_rows ?? '-'}</span>
        </div>
        <div className="p3-ds-stat-card">
          <span className="label">列数</span>
          <span className="value">{report.summary?.num_columns ?? '-'}</span>
        </div>
        <div className="p3-ds-stat-card">
          <span className="label">缺失单元</span>
          <span className="value">{report.summary?.num_missing ?? '-'}</span>
        </div>
        <div className="p3-ds-stat-card">
          <span className="label">重复行</span>
          <span className="value green">{report.summary?.duplicate_rows ?? '-'}</span>
        </div>
      </div>

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

      {report.correlations && Object.keys(report.correlations).length > 0 ? (
        <Card title="相关性矩阵（数值列）" size="small" style={{ marginBottom: 16 }}>
          <Table
            size="small"
            pagination={false}
            rowKey="col"
            columns={[
              { title: '列', dataIndex: 'col', key: 'col', width: 120 },
              ...Object.keys(report.correlations).map((c) => ({
                title: c,
                dataIndex: c,
                key: c,
                render: (v: number | undefined) => (v != null ? v.toFixed(3) : '-'),
              })),
            ]}
            dataSource={Object.entries(report.correlations).map(([col, vals]) => ({
              col,
              ...vals,
            }))}
            scroll={{ x: true }}
          />
        </Card>
      ) : null}

      <Typography.Title level={5} style={{ marginBottom: 12 }}>
        可视化
      </Typography.Title>
      {(report.visualizations ?? []).length === 0 ? (
        <Text type="secondary">未包含图表，请重新运行 EDA 并勾选可视化</Text>
      ) : (
        <div className="p3-ds-chart-grid">
          {(report.visualizations ?? []).map((viz, idx) => {
            const opt = mergeEChartsOption(viz)
            if (!opt) return null
            return (
              <Card key={`${viz.title}-${idx}`} title={viz.title} size="small">
                <ReactECharts option={opt} style={{ height: chartHeight(viz), width: '100%' }} notMerge lazyUpdate />
              </Card>
            )
          })}
        </div>
      )}
    </>
  )

  return (
    <div className="p3-ds-body">
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="EDA 仅支持 CSV / JSON 数据集"
        description="请先选择表格数据集并点击「运行 EDA」；图表数据来自后端 pandas 统计。"
      />

      <div className="p3-ds-eda-layout">
        <aside className="p3-ds-sidebar-panel">
          <h4>
            数据筛选 <span className="p3-ds-badge hot">EDA</span>
          </h4>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <div>
              <Text type="secondary" style={{ display: 'block', marginBottom: 6 }}>
                数据集
              </Text>
              <Select
                allowClear
                showSearch
                optionFilterProp="label"
                placeholder="选择 CSV / JSON"
                style={{ width: '100%' }}
                options={dsOptions}
                value={datasetId}
                onChange={(v) => {
                  setDatasetId(v)
                  setLocalReport(null)
                  setShouldFetchReport(false)
                }}
                loading={datasetsQuery.isLoading}
              />
            </div>
            <Button
              type="primary"
              block
              disabled={!datasetId}
              loading={runMut.isPending}
              onClick={() => {
                if (!datasetId) return
                runMut.mutate()
              }}
            >
              运行 EDA
            </Button>
            <Button
              block
              disabled={!datasetId}
              loading={reportQuery.isFetching}
              onClick={() => {
                if (!datasetId) return
                setShouldFetchReport(true)
                void reportQuery.refetch()
              }}
            >
              刷新报告
            </Button>
          </Space>
        </aside>

        <section>{mainContent}</section>
      </div>
    </div>
  )
}
