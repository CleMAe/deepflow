import api, { type ApiResponse } from '@/lib/axios'
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
  const res = (await api.get('/models/library', { params })) as ApiResponse<LibraryModel[]>
  return res.data
}

export async function getModelLibraryDetail(modelId: string) {
  const res = (await api.get(`/models/library/${modelId}`)) as ApiResponse<LibraryModel>
  return res.data
}

export async function listProjectModels(projectId: string, page = 1, pageSize = 20) {
  const res = (await api.get(`/projects/${projectId}/models`, {
    params: { page, page_size: pageSize },
  })) as ApiResponse<PaginatedModels>
  return res.data
}

export async function createProjectModel(projectId: string, payload: ModelCreate) {
  const res = (await api.post(`/projects/${projectId}/models`, payload)) as ApiResponse<Model>
  return res.data
}

export async function getProjectModel(projectId: string, modelId: string) {
  const res = (await api.get(`/projects/${projectId}/models/${modelId}`)) as ApiResponse<Model>
  return res.data
}

export async function updateProjectModel(projectId: string, modelId: string, payload: ModelUpdate) {
  const res = (await api.put(`/projects/${projectId}/models/${modelId}`, payload)) as ApiResponse<Model>
  return res.data
}

export async function validateModelConfig(
  projectId: string,
  modelId: string,
  payload: ModelValidateRequest
) {
  const res = (await api.post(
    `/projects/${projectId}/models/${modelId}/validate`,
    payload
  )) as ApiResponse<ValidationResult>
  return res.data
}
