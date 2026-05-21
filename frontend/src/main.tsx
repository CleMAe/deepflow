import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { p3UseMock } from '@/config/p3Api'
import './index.css'
import './styles/p3-dropship.css'
import App from './App'
import { shouldEnableMsw } from './config/env'

async function enableMocking() {
  if (shouldEnableMsw()) {
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
