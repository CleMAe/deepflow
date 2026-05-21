import { useState } from 'react'
import { Card, Row, Col, List, Button, Modal, Form, Input, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api, { type ApiResponse } from '@/lib/axios'
import type { components } from '@/api/types'

type PaginatedProjects = components['schemas']['PaginatedProjects']
type Project = components['schemas']['Project']
type ProjectCreate = components['schemas']['ProjectCreate']

export default function DashboardPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  const [open, setOpen] = useState(false)
  const [form] = Form.useForm<ProjectCreate>()
  const [loading, setLoading] = useState(false)

  const { data } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const res = await api.get('/projects')
      return (res as unknown as ApiResponse<PaginatedProjects>).data as PaginatedProjects
    },
  })

  const handleCreate = async (values: ProjectCreate) => {
    setLoading(true)
    try {
      await api.post('/projects', values)
      messageApi.success('项目创建成功')
      setOpen(false)
      form.resetFields()
      void queryClient.invalidateQueries({ queryKey: ['projects'] })
    } catch {
      messageApi.error('项目创建失败')
    } finally {
      setLoading(false)
    }
  }

  const items = data?.items || []

  return (
    <div>
      {contextHolder}
      <h2 style={{ marginBottom: 24 }}>工作台</h2>
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="我的项目" extra={<Button type="primary" onClick={() => setOpen(true)}>新建项目</Button>}>
            <List
              dataSource={items}
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

      <Modal
        title="新建项目"
        open={open}
        onCancel={() => { setOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        confirmLoading={loading}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="请输入项目名称" />
          </Form.Item>
          <Form.Item name="description" label="项目描述">
            <Input.TextArea placeholder="请输入项目描述" rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
