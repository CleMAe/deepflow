import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { p3UseMock } from '@/config/p3Api'
import './index.css'
import App from './App'

async function enableMocking() {
  if (import.meta.env.DEV) {
    const { worker } = await import('./mocks/browser')
    return worker.start({
      onUnhandledRequest: 'bypass',
    }).then(() => {
      if (!p3UseMock) {
        console.info('[P3] MSW disabled for datasets/cleaning/EDA — using backend API')
      }
    })
  }
  return Promise.resolve()
}

enableMocking().then(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>
  )
})
