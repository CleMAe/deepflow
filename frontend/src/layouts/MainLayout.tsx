import { useState } from 'react'
import { Layout, Menu, Button, Avatar, Dropdown } from 'antd'
import { Outlet, useNavigate, useLocation, useParams } from 'react-router-dom'
import {
  DashboardOutlined,
  DatabaseOutlined,
  ClearOutlined,
  BuildOutlined,
  ThunderboltOutlined,
  RobotOutlined,
  ExperimentOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import { useUserStore } from '@/stores/userStore'

const { Header, Sider, Content } = Layout

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { projectId } = useParams()
  const [collapsed, setCollapsed] = useState(false)
  const logout = useUserStore((s) => s.logout)

  const projectItems = projectId
    ? [
        {
          key: `/projects/${projectId}/data`,
          icon: <DatabaseOutlined />,
          label: '数据管理',
        },
        {
          key: `/projects/${projectId}/cleaning`,
          icon: <ClearOutlined />,
          label: '清洗 & EDA',
        },
        {
          key: `/projects/${projectId}/models`,
          icon: <BuildOutlined />,
          label: '模型构建',
        },
        {
          key: `/projects/${projectId}/training`,
          icon: <ThunderboltOutlined />,
          label: '训练监控',
        },
        {
          key: `/projects/${projectId}/inference`,
          icon: <ExperimentOutlined />,
          label: '推理测试',
        },
        {
          key: `/projects/${projectId}/agents`,
          icon: <RobotOutlined />,
          label: 'Agent',
        },
      ]
    : []

  const items = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '工作台',
    },
    ...projectItems,
  ]

  const selectedKey = location.pathname

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed} theme="light">
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 18 }}>
          DeepFlow
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={items}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <Dropdown
            menu={{
              items: [
                { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: logout },
              ],
            }}
          >
            <Avatar icon={<UserOutlined />} style={{ cursor: 'pointer' }} />
          </Dropdown>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
