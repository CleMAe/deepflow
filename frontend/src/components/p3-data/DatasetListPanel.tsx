import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Input, Select, Space, Tag, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import DataTable from '@/components/common/DataTable'
import { listDatasets, type Dataset } from '@/api/datasets'
import { formatPagination } from '@/utils/formatPagination'
import {
  DATASET_FORMAT_OPTIONS,
  DATASET_STATUS_OPTIONS,
  formatDatasetFormat,
  formatDatasetStatus,
} from '@/components/p3-data/datasetLabels'

const { Search } = Input

interface DatasetListPanelProps {
  projectId: string
}

function formatDate(value?: string) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function statusColor(status?: Dataset['status']) {
  switch (status) {
    case 'ready':
      return 'green'
    case 'cleaned':
      return 'blue'
    case 'uploading':
    case 'cleaning':
      return 'processing'
    case 'error':
      return 'red'
    default:
      return 'default'
  }
}

export default function DatasetListPanel({ projectId }: DatasetListPanelProps) {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')
  const [format, setFormat] = useState<Dataset['format']>()
  const [status, setStatus] = useState<Dataset['status']>()

  const datasetsQuery = useQuery({
    queryKey: ['p3-datasets', projectId, page, pageSize, search, format, status],
    queryFn: () =>
      listDatasets(projectId, {
        page,
        page_size: pageSize,
        search: search || undefined,
        format,
        status,
      }),
    enabled: !!projectId,
  })

  const pagination = useMemo(() => {
    const total = datasetsQuery.data?.total ?? 0
    return formatPagination({ page, pageSize, total })
  }, [datasetsQuery.data?.total, page, pageSize])

  const columns: ColumnsType<Dataset> = [
    { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
    {
      title: '格式',
      dataIndex: 'format',
      key: 'format',
      width: 90,
      render: (value: Dataset['format']) => formatDatasetFormat(value),
    },
    {
      title: '样本数',
      dataIndex: 'num_samples',
      key: 'num_samples',
      width: 100,
      render: (value?: number) => (value != null ? value.toLocaleString() : '-'),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (value: Dataset['status']) => (
        <Tag color={statusColor(value)}>{formatDatasetStatus(value)}</Tag>
      ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags?: string[]) =>
        tags?.length ? (
          <Space size={[0, 4]} wrap>
            {tags.map((tag) => (
              <Tag key={tag}>{tag}</Tag>
            ))}
          </Space>
        ) : (
          <Typography.Text type="secondary">-</Typography.Text>
        ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (value?: string) => formatDate(value),
    },
  ]

  return (
    <div>
      <Space wrap style={{ marginBottom: 16 }}>
        <Search
          allowClear
          placeholder="搜索名称或标签"
          style={{ width: 240 }}
          onSearch={(value) => {
            setPage(1)
            setSearch(value.trim())
          }}
        />
        <Select
          allowClear
          placeholder="格式"
          style={{ width: 120 }}
          options={DATASET_FORMAT_OPTIONS}
          value={format}
          onChange={(value) => {
            setPage(1)
            setFormat(value)
          }}
        />
        <Select
          allowClear
          placeholder="状态"
          style={{ width: 120 }}
          options={DATASET_STATUS_OPTIONS}
          value={status}
          onChange={(value) => {
            setPage(1)
            setStatus(value)
          }}
        />
      </Space>

      <DataTable<Dataset>
        rowKey="id"
        columns={columns}
        dataSource={datasetsQuery.data?.items ?? []}
        loading={datasetsQuery.isLoading}
        pagination={{
          current: pagination.page,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (nextPage, nextPageSize) => {
            setPage(nextPage)
            setPageSize(nextPageSize)
          },
        }}
      />
    </div>
  )
}
