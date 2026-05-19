import { Link, useParams } from 'react-router-dom'
import { Alert, Card } from 'antd'

export default function ProjectTrainingPage() {
  const { projectId = '' } = useParams()

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>训练监控</h2>
      <Card>
        <Alert
          type="info"
          showIcon
          message="训练任务与实时监控将于 Day2 实现"
          description={
            <>
              计划包含：训练任务创建/列表、启停控制、WebSocket 实时曲线与日志流。
              请先完成{' '}
              <Link to={`/projects/${projectId}/models`}>模型构建与参数配置</Link>。
            </>
          }
        />
      </Card>
    </div>
  )
}
