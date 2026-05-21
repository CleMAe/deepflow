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
    <div className="p3-ds-page">
      <header className="p3-ds-hero">
        <h1>
          数据清洗 · <span className="p3-ds-accent">EDA</span> · 增强
        </h1>
        <p className="p3-ds-hero-desc">
          像选品一样管理表格数据：清洗、探索性分析、图像增强，一站式完成上传后的数据处理。
        </p>
      </header>
      <Card className="p3-ds-tabs-wrap" bordered={false}>
        <Tabs items={items} size="large" />
      </Card>
    </div>
  )
}
