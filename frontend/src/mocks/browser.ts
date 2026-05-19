import { setupWorker } from 'msw/browser'
import { authHandlers } from './handlers/auth'
import { projectHandlers } from './handlers/projects'
import { datasetHandlers } from './handlers/datasets'

export const worker = setupWorker(...authHandlers, ...projectHandlers, ...datasetHandlers)
