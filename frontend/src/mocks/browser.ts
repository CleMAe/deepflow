import { setupWorker } from 'msw/browser'
import { authHandlers } from './handlers/auth'
import { projectHandlers } from './handlers/projects'
import { datasetHandlers } from './handlers/datasets'
import { inferenceHandlers } from './handlers/inference'
import { agentHandlers } from './handlers/agents'
import { modelHandlers } from './handlers/models'
import { trainingHandlers } from './handlers/training'
import { experimentHandlers } from './handlers/experiments'

export const worker = setupWorker(
  ...authHandlers,
  ...projectHandlers,
  ...datasetHandlers,
  ...inferenceHandlers,
  ...agentHandlers,
  ...modelHandlers,
  ...trainingHandlers,
  ...experimentHandlers,
)
