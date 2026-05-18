import { Card, Tabs } from 'antd'

export default function ProjectCleaningPage() {
  const items = [
    { key: 'clean', label: '数据清洗', children: <p>缺失值 / 异常值 / 去重 / 编码转换（P3 待实现）</p> },
    { key: 'eda', label: 'EDA 报告', children: <p>统计概览与可视化（P3 待实现）</p> },
    { key: 'augment', label: '数据增强', children: <p>CV 增强参数配置（P3 待实现）</p> },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据清洗 & EDA</h2>
      <Card>
        <Tabs items={items} />
      </Card>
    </div>
  )
}
