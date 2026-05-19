import api from '@/lib/axios'
import type { components } from '@/api/types'

export type LibraryModel = components['schemas']['LibraryModel']
export type Model = components['schemas']['Model']
export type ModelCreate = components['schemas']['ModelCreate']
export type ModelUpdate = components['schemas']['ModelUpdate']
export type ModelValidateRequest = components['schemas']['ModelValidateRequest']
export type ValidationResult = components['schemas']['ValidationResult']
export type PaginatedModels = components['schemas']['PaginatedModels']

export type ModelLibraryQuery = {
  task_type?: LibraryModel['task_type']
  search?: string
}

export async function listModelLibrary(params?: ModelLibraryQuery) {
  const res = await api.get('/models/library', { params })
  return res as unknown as LibraryModel[]
}

export async function getModelLibraryDetail(modelId: string) {
  const res = await api.get(`/models/library/${modelId}`)
  return res as unknown as LibraryModel
}

export async function listProjectModels(projectId: string, page = 1, pageSize = 20) {
  const res = await api.get(`/projects/${projectId}/models`, {
    params: { page, page_size: pageSize },
  })
  return res as unknown as PaginatedModels
}

export async function createProjectModel(projectId: string, payload: ModelCreate) {
  const res = await api.post(`/projects/${projectId}/models`, payload)
  return res as unknown as Model
}

export async function getProjectModel(projectId: string, modelId: string) {
  const res = await api.get(`/projects/${projectId}/models/${modelId}`)
  return res as unknown as Model
}

export async function updateProjectModel(projectId: string, modelId: string, payload: ModelUpdate) {
  const res = await api.put(`/projects/${projectId}/models/${modelId}`, payload)
  return res as unknown as Model
}

export async function validateModelConfig(
  projectId: string,
  modelId: string,
  payload: ModelValidateRequest
) {
  const res = await api.post(`/projects/${projectId}/models/${modelId}/validate`, payload)
  return res as unknown as ValidationResult
}
