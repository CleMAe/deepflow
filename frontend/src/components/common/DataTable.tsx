import { Empty, Table } from 'antd'
import type { TableProps } from 'antd/es/table'

interface DataTableProps<T> extends TableProps<T> {
  loading?: boolean
}

export default function DataTable<T extends Record<string, unknown>>({
  loading,
  locale,
  ...props
}: DataTableProps<T>) {
  const normalizedLoading =
    typeof loading === 'boolean' ? { spinning: loading, tip: '加载中' } : loading

  return (
    <Table
      loading={normalizedLoading}
      rowKey="id"
      pagination={{ showSizeChanger: true, defaultPageSize: 20 }}
      locale={{
        emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" />,
        ...locale,
      }}
      scroll={{ x: 'max-content' }}
      {...props}
    />
  )
}
