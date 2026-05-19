import { useEffect } from 'react'
import { Card, Row, Col, List, Button } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api, { type ApiResponse } from '@/lib/axios'
import { useProjectStore } from '@/stores/projectStore'
import type { components } from '@/api/types'

type PaginatedProjects = components['schemas']['PaginatedProjects']
type Project = components['schemas']['Project']

export default function DashboardPage() {
  const navigate = useNavigate()
  const setProjects = useProjectStore((s) => s.setProjects)

  const { data } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const res = await api.get('/projects')
      return (res as ApiResponse<PaginatedProjects>).data as PaginatedProjects
    },
  })

  useEffect(() => {
    if (data?.items) {
      setProjects(data.items)
    }
  }, [data, setProjects])

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>工作台</h2>
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="我的项目" extra={<Button type="primary">新建项目</Button>}>
            <List
              dataSource={data?.items || []}
              renderItem={(item: Project) => (
                <List.Item
                  actions={[
                    <Button key="enter" type="link" onClick={() => navigate(`/projects/${item.id}/data`)}>
                      进入
                    </Button>,
                  ]}
                >
                  <List.Item.Meta title={item.name} description={item.description} />
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="快速开始">
            <p>1. 创建或选择一个项目</p>
            <p>2. 上传数据集</p>
            <p>3. 进行数据清洗与 EDA</p>
            <p>4. 选择模型并配置参数</p>
            <p>5. 启动训练并监控</p>
            <p>6. 推理测试与 Agent 构建</p>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
