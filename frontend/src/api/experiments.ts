import api, { type ApiResponse } from '@/lib/axios'
import type { components } from '@/api/types'

export type Experiment = components['schemas']['Experiment']
export type ExperimentUpdate = components['schemas']['ExperimentUpdate']
export type ExperimentComparison = components['schemas']['ExperimentComparison']
export type PaginatedExperiments = components['schemas']['PaginatedExperiments']

function unwrap<T>(res: unknown): T {
  const envelope = res as ApiResponse<T>
  if (envelope.code !== 0) {
    throw new Error(envelope.message || '请求失败')
  }
  return envelope.data as T
}

export async function listExperiments(projectId: string, page = 1, pageSize = 20) {
  const res = await api.get(`/projects/${projectId}/experiments`, {
    params: { page, page_size: pageSize },
  })
  return unwrap<PaginatedExperiments>(res)
}

export async function getExperiment(projectId: string, expId: string) {
  const res = await api.get(`/projects/${projectId}/experiments/${expId}`)
  return unwrap<Experiment>(res)
}

export async function updateExperiment(projectId: string, expId: string, payload: ExperimentUpdate) {
  const res = await api.put(`/projects/${projectId}/experiments/${expId}`, payload)
  return unwrap<Experiment>(res)
}

export async function compareExperiments(projectId: string, experimentIds: string[]) {
  const res = await api.post(`/projects/${projectId}/experiments/compare`, {
    experiment_ids: experimentIds,
  })
  return unwrap<ExperimentComparison>(res)
}
