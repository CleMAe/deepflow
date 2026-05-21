import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import MainLayout from '../MainLayout'

describe('MainLayout', () => {
  it('renders shared layout containers for responsive polish', async () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route element={<MainLayout />}>
            <Route path="/dashboard" element={<div>Dashboard content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('DeepFlow')).toBeInTheDocument()
      expect(screen.getByText('Dashboard content')).toBeInTheDocument()
      expect(container.querySelector('.deepflow-layout')).toBeInTheDocument()
      expect(container.querySelector('.deepflow-content')).toBeInTheDocument()
    })
  })
})
