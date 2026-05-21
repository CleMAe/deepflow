import { setupWorker } from 'msw/browser'
import { p3UseMock } from '@/config/p3Api'
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

/** P3 + 项目列表：联调时走真实 API，避免 MSW 假项目 ID 导致数据集为空 */
const p3Handlers = p3UseMock
  ? [...datasetHandlers, ...p3Day2Handlers, ...p3CleaningHandlers]
  : []

const projectHandlersForWorker = p3UseMock ? projectHandlers : []

export const worker = setupWorker(
  ...authHandlers,
  ...projectHandlersForWorker,
  ...p3Handlers,
  ...modelsHandlers,
  ...inferenceHandlers,
  ...agentHandlers,
  ...trainingHandlers,
  ...experimentHandlers,
)
