import { Card, Empty, Tabs } from 'antd'
import { useParams } from 'react-router-dom'
import AugmentationTab from '@/components/p3-data/AugmentationTab'
import CleaningOperationsTab from '@/components/p3-data/CleaningOperationsTab'
import EdaReportTab from '@/components/p3-data/EdaReportTab'

export default function ProjectCleaningPage() {
  const { projectId } = useParams()

  if (!projectId) {
    return <Empty description="缺少项目 ID" />
  }

  const items = [
    {
      key: 'clean',
      label: '数据清洗',
      children: <CleaningOperationsTab projectId={projectId} />,
    },
    {
      key: 'eda',
      label: 'EDA 报告',
      children: <EdaReportTab projectId={projectId} />,
    },
    {
      key: 'augment',
      label: '数据增强',
      children: <AugmentationTab projectId={projectId} />,
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据清洗 · EDA · 数据增强</h2>
      <Card>
        <Tabs items={items} />
      </Card>
    </div>
  )
}
