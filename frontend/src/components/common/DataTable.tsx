import { Table } from 'antd'
import type { TableProps } from 'antd/es/table'

interface DataTableProps<T> extends TableProps<T> {
  loading?: boolean
}

export default function DataTable<T extends Record<string, unknown>>({
  loading,
  ...props
}: DataTableProps<T>) {
  return (
    <Table
      loading={loading}
      rowKey="id"
      pagination={{ showSizeChanger: true, defaultPageSize: 20 }}
      scroll={{ x: 'max-content' }}
      {...props}
    />
  )
}
