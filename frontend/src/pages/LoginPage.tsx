import { useState } from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import api, { type ApiResponse } from '@/lib/axios'
import { useUserStore } from '@/stores/userStore'
import type { components } from '@/api/types'

type TokenPair = components['schemas']['TokenPair']

export default function LoginPage() {
  const navigate = useNavigate()
  const setToken = useUserStore((s) => s.setToken)
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const res = await api.post('/auth/login', values)
      const data = (res as unknown as ApiResponse<TokenPair>).data
      setToken(data?.access_token ?? null)
      localStorage.setItem('refresh_token', data?.refresh_token ?? '')
      message.success('登录成功')
      navigate('/dashboard')
    } catch {
      message.error('登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
      <Card title="DeepFlow 登录" style={{ width: 400 }}>
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item label="用户名" name="username" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="密码" name="password" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
          <Form.Item style={{ textAlign: 'center', marginBottom: 0 }}>
            <Button type="link" onClick={() => navigate('/register')}>
              还没有账号？去注册
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
