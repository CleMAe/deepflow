import api, { type ApiResponse } from '@/lib/axios'
import type { components } from '@/api/types'

export type Dataset = components['schemas']['Dataset']
export type EvaluateRequest = components['schemas']['EvaluateRequest']
export type EvaluateResult = components['schemas']['EvaluateResult']
export type Model = components['schemas']['Model']
export type OnlineInferenceRequest = components['schemas']['OnlineInferenceRequest']
export type OnlineInferenceResult = components['schemas']['OnlineInferenceResult']
export type PaginatedDatasets = components['schemas']['PaginatedDatasets']
export type PaginatedModels = components['schemas']['PaginatedModels']

export async function listInferenceDatasets(projectId: string) {
  const res = await api.get(`/projects/${projectId}/datasets`)
  return (res as unknown as ApiResponse<PaginatedDatasets>).data
}

export async function listInferenceModels(projectId: string) {
  const res = await api.get(`/projects/${projectId}/models`)
  return (res as unknown as ApiResponse<PaginatedModels>).data
}

export async function evaluateModel(projectId: string, payload: EvaluateRequest) {
  const res = await api.post(`/projects/${projectId}/inference/evaluate`, payload)
  return (res as unknown as ApiResponse<EvaluateResult>).data
}

export async function runOnlineInference(projectId: string, payload: OnlineInferenceRequest) {
  const res = await api.post(`/projects/${projectId}/inference/online`, payload)
  return (res as unknown as ApiResponse<OnlineInferenceResult>).data
}
