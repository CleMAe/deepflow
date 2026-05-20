import { useParams } from 'react-router-dom'
import { Empty } from 'antd'
import DataManagementView from '@/components/p3-data/DataManagementView'

export default function ProjectDataPage() {
  const { projectId } = useParams()

  if (!projectId) {
    return <Empty description="缺少项目 ID" />
  }

  return <DataManagementView projectId={projectId} />
}
