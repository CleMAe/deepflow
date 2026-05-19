import { Card, Empty } from 'antd'
import { useParams } from 'react-router-dom'
import DatasetListPanel from '@/components/p3-data/DatasetListPanel'
import DatasetUploadPanel from '@/components/p3-data/DatasetUploadPanel'

export default function ProjectDataPage() {
  const { projectId } = useParams()

  if (!projectId) {
    return <Empty description="缺少项目 ID" />
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据管理</h2>
      <Card title="数据上传" style={{ marginBottom: 16 }}>
        <DatasetUploadPanel projectId={projectId} />
      </Card>
      <Card title="数据集列表">
        <DatasetListPanel projectId={projectId} />
      </Card>
    </div>
  )
}
