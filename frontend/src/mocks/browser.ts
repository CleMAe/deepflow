import { setupWorker } from 'msw/browser'
import { authHandlers } from './handlers/auth'
import { projectHandlers } from './handlers/projects'
import { datasetHandlers } from './handlers/datasets'
import { modelsHandlers } from './handlers/models'
import { inferenceHandlers } from './handlers/inference'

export const worker = setupWorker(
  ...authHandlers,
  ...projectHandlers,
  ...datasetHandlers,
  ...modelsHandlers,
  ...inferenceHandlers
)
