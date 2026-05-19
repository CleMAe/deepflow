import api from '@/lib/axios'
import type { components } from '@/api/types'

export type Dataset = components['schemas']['Dataset']
export type BatchInferenceRequest = components['schemas']['BatchInferenceRequest']
export type EvaluateRequest = components['schemas']['EvaluateRequest']
export type EvaluateResult = components['schemas']['EvaluateResult']
export type InferenceTask = components['schemas']['InferenceTask']
export type Model = components['schemas']['Model']
export type OnlineInferenceRequest = components['schemas']['OnlineInferenceRequest']
export type OnlineInferenceResult = components['schemas']['OnlineInferenceResult']
export type PaginatedDatasets = components['schemas']['PaginatedDatasets']
export type PaginatedModels = components['schemas']['PaginatedModels']

export async function listInferenceDatasets(projectId: string) {
  const res = await api.get(`/projects/${projectId}/datasets`)
  return res as unknown as PaginatedDatasets
}

export async function listInferenceModels(projectId: string) {
  const res = await api.get(`/projects/${projectId}/models`)
  return res as unknown as PaginatedModels
}

export async function evaluateModel(projectId: string, payload: EvaluateRequest) {
  const res = await api.post(`/projects/${projectId}/inference/evaluate`, payload)
  return res as unknown as EvaluateResult
}

export async function runBatchInference(projectId: string, payload: BatchInferenceRequest) {
  const res = await api.post(`/projects/${projectId}/inference/batch`, payload)
  return res as unknown as InferenceTask
}

export async function getInferenceResult(projectId: string, taskId: string) {
  const res = await api.get(`/projects/${projectId}/inference/${taskId}`)
  return res as unknown as InferenceTask
}

export async function runOnlineInference(projectId: string, payload: OnlineInferenceRequest) {
  const res = await api.post(`/projects/${projectId}/inference/online`, payload)
  return res as unknown as OnlineInferenceResult
}
