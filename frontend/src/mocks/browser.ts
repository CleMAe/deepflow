import { setupWorker } from 'msw/browser'
import { authHandlers } from './handlers/auth'
import { projectHandlers } from './handlers/projects'
import { datasetHandlers } from './handlers/datasets'
import { p3DataHandlers } from './handlers/p3DataHandlers'
import { inferenceHandlers } from './handlers/inference'
import { agentHandlers } from './handlers/agents'

export const worker = setupWorker(
  ...authHandlers,
  ...projectHandlers,
  ...p3DataHandlers,
  ...datasetHandlers,
  ...inferenceHandlers,
  ...agentHandlers,
)
