import api, { type ApiResponse } from '@/lib/axios'
import type { components } from '@/api/types'

export type TrainingJob = components['schemas']['TrainingJob']
export type TrainingJobCreate = components['schemas']['TrainingJobCreate']
export type TrainingStatus = components['schemas']['TrainingStatus']
export type PaginatedTrainingJobs = components['schemas']['PaginatedTrainingJobs']
export type Checkpoint = components['schemas']['Checkpoint']

function unwrap<T>(res: unknown): T {
  const envelope = res as ApiResponse<T>
  if (envelope.code !== 0) {
    throw new Error(envelope.message || '请求失败')
  }
  return envelope.data as T
}

export async function listTrainingJobs(projectId: string, page = 1, pageSize = 20) {
  const res = await api.get(`/projects/${projectId}/training-jobs`, {
    params: { page, page_size: pageSize },
  })
  return unwrap<PaginatedTrainingJobs>(res)
}

export async function createTrainingJob(projectId: string, payload: TrainingJobCreate) {
  const res = await api.post(`/projects/${projectId}/training-jobs`, payload)
  return unwrap<TrainingJob>(res)
}

export async function getTrainingJob(projectId: string, jobId: string) {
  const res = await api.get(`/projects/${projectId}/training-jobs/${jobId}`)
  return unwrap<TrainingJob>(res)
}

export async function startTrainingJob(projectId: string, jobId: string) {
  const res = await api.post(`/projects/${projectId}/training-jobs/${jobId}/start`)
  return unwrap<TrainingJob>(res)
}

export async function pauseTrainingJob(projectId: string, jobId: string) {
  const res = await api.post(`/projects/${projectId}/training-jobs/${jobId}/pause`)
  return unwrap<TrainingJob>(res)
}

export async function resumeTrainingJob(projectId: string, jobId: string) {
  const res = await api.post(`/projects/${projectId}/training-jobs/${jobId}/resume`)
  return unwrap<TrainingJob>(res)
}

export async function stopTrainingJob(projectId: string, jobId: string) {
  const res = await api.post(`/projects/${projectId}/training-jobs/${jobId}/stop`)
  return unwrap<TrainingJob>(res)
}

export async function getTrainingLogs(projectId: string, jobId: string, tail = 200) {
  const res = await api.get(`/projects/${projectId}/training-jobs/${jobId}/logs`, {
    params: { tail },
  })
  return unwrap<{ logs?: string[] }>(res)
}

export async function listCheckpoints(projectId: string, jobId: string) {
  const res = await api.get(`/projects/${projectId}/training-jobs/${jobId}/checkpoints`)
  return unwrap<{ checkpoints?: Checkpoint[] }>(res)
}
