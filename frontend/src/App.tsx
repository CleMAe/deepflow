import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { Suspense, lazy } from 'react'
import { ConfigProvider, Spin } from 'antd'
import { queryClient } from '@/lib/queryClient'
import { themeConfig } from '@/theme'
import RequireAuth from '@/components/auth/RequireAuth'
import MainLayout from '@/layouts/MainLayout'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'

const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const ProjectDataPage = lazy(() => import('@/pages/ProjectDataPage'))
const ProjectCleaningPage = lazy(() => import('@/pages/ProjectCleaningPage'))
const ProjectModelsPage = lazy(() => import('@/pages/ProjectModelsPage'))
const ProjectTrainingPage = lazy(() => import('@/pages/ProjectTrainingPage'))
const ProjectInferencePage = lazy(() => import('@/pages/ProjectInferencePage'))
const ProjectAgentsPage = lazy(() => import('@/pages/ProjectAgentsPage'))

function App() {
  return (
    <ConfigProvider theme={themeConfig}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Suspense fallback={<Spin size="large" style={{ display: 'flex', justifyContent: 'center', marginTop: 200 }} />}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route element={<RequireAuth><MainLayout /></RequireAuth>}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/projects/:projectId/data" element={<ProjectDataPage />} />
                <Route path="/projects/:projectId/cleaning" element={<ProjectCleaningPage />} />
                <Route path="/projects/:projectId/models" element={<ProjectModelsPage />} />
                <Route path="/projects/:projectId/training" element={<ProjectTrainingPage />} />
                <Route path="/projects/:projectId/inference" element={<ProjectInferencePage />} />
                <Route path="/projects/:projectId/agents" element={<ProjectAgentsPage />} />
              </Route>
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </QueryClientProvider>
    </ConfigProvider>
  )
}

export default App
