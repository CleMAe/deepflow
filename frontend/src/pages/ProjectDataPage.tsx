import { Card, Upload, Table } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import api from '@/lib/axios'
import type { components } from '@/api/types'

type PaginatedDatasets = components['schemas']['PaginatedDatasets']

export default function ProjectDataPage() {
  const { projectId } = useParams()

  const { data } = useQuery({
    queryKey: ['datasets', projectId],
    queryFn: async () => {
      const res = await api.get(`/projects/${projectId}/datasets`)
      return (res as { data: PaginatedDatasets }).data
    },
    enabled: !!projectId,
  })

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '格式', dataIndex: 'format', key: 'format' },
    { title: '样本数', dataIndex: 'num_samples', key: 'num_samples' },
    { title: '状态', dataIndex: 'status', key: 'status' },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据管理</h2>
      <Card style={{ marginBottom: 16 }}>
        <Upload.Dragger name="file" action={`/api/v1/projects/${projectId}/datasets/upload`} multiple>
          <p className="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p>点击或拖拽文件到此处上传</p>
        </Upload.Dragger>
      </Card>
      <Card title="数据集列表">
        <Table rowKey="id" columns={columns} dataSource={data?.items || []} />
      </Card>
    </div>
  )
}
