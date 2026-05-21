import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import DataTable from '../DataTable'

type Row = {
  id: string
  name: string
}

const columns = [{ title: '名称', dataIndex: 'name', key: 'name' }]

describe('DataTable', () => {
  it('shows the shared empty state when there is no data', () => {
    render(<DataTable<Row> columns={columns} dataSource={[]} />)

    expect(screen.getByText('暂无数据')).toBeInTheDocument()
  })

  it('keeps page-specific empty state text when locale is provided', () => {
    render(
      <DataTable<Row>
        columns={columns}
        dataSource={[]}
        locale={{ emptyText: '暂无训练任务，请创建新任务' }}
      />,
    )

    expect(screen.getByText('暂无训练任务，请创建新任务')).toBeInTheDocument()
  })

  it('shows the shared loading tip when loading is true', () => {
    render(<DataTable<Row> columns={columns} dataSource={[]} loading />)

    expect(screen.getByText('加载中')).toBeInTheDocument()
  })
})
