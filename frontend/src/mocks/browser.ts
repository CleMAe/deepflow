import { setupWorker } from 'msw/browser'
import { authHandlers } from './handlers/auth'
import { projectHandlers } from './handlers/projects'
import { datasetHandlers } from './handlers/datasets'
import { modelsHandlers } from './handlers/models'
import { inferenceHandlers } from './handlers/inference'
import { agentHandlers } from './handlers/agents'
import { trainingHandlers } from './handlers/training'
import { experimentHandlers } from './handlers/experiments'

export const worker = setupWorker(
  ...authHandlers,
  ...projectHandlers,
  ...datasetHandlers,
  ...modelsHandlers,
  ...inferenceHandlers,
  ...agentHandlers,
  ...trainingHandlers,
  ...experimentHandlers,
)
