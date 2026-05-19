import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'
import MainLayout from '@/layouts/MainLayout'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import DashboardPage from '@/pages/DashboardPage'
import ProjectDataPage from '@/pages/ProjectDataPage'
import ProjectCleaningPage from '@/pages/ProjectCleaningPage'
import ProjectModelsPage from '@/pages/ProjectModelsPage'
import ProjectTrainingPage from '@/pages/ProjectTrainingPage'
import ProjectInferencePage from '@/pages/ProjectInferencePage'
import ProjectAgentsPage from '@/pages/ProjectAgentsPage'

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<MainLayout />}>
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
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
