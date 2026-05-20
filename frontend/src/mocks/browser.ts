import { setupWorker } from 'msw/browser'
import { authHandlers } from './handlers/auth'
import { projectHandlers } from './handlers/projects'
import { datasetHandlers } from './handlers/datasets'
import { modelsHandlers } from './handlers/models'
import { inferenceHandlers } from './handlers/inference'
import { agentHandlers } from './handlers/agents'
import { trainingHandlers } from './handlers/training'
import { experimentHandlers } from './handlers/experiments'
import { p3Day2Handlers } from './handlers/p3Day2Handlers'
import { p3CleaningHandlers } from './handlers/p3CleaningHandlers'

export const worker = setupWorker(
  ...authHandlers,
  ...projectHandlers,
  ...datasetHandlers,
  ...p3Day2Handlers,
  ...p3CleaningHandlers,
  ...modelsHandlers,
  ...inferenceHandlers,
  ...agentHandlers,
  ...trainingHandlers,
  ...experimentHandlers,
)
