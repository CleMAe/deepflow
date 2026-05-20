import api, { type ApiResponse } from '@/lib/axios'
import type { components } from '@/api/types'

export type CleanMissingRequest = components['schemas']['CleanMissingRequest']
export type CleanOutlierRequest = components['schemas']['CleanOutlierRequest']
export type CleanDedupRequest = components['schemas']['CleanDedupRequest']
export type CleanEncodeRequest = components['schemas']['CleanEncodeRequest']
export type CleanTypeConvertRequest = components['schemas']['CleanTypeConvertRequest']
export type CleaningResult = components['schemas']['CleaningResult']
export type EDARequest = components['schemas']['EDARequest']
export type EDAReport = components['schemas']['EDAReport']
export type AugmentRequest = components['schemas']['AugmentRequest']
export type AugmentResult = components['schemas']['AugmentResult']
export type AugmentTransform = components['schemas']['AugmentTransform']

function unwrap<T>(res: unknown): T {
  return (res as ApiResponse<T>).data as T
}

export async function cleanMissing(projectId: string, datasetId: string, body: CleanMissingRequest) {
  const res = await api.post(`/projects/${projectId}/datasets/${datasetId}/clean/missing`, body)
  return unwrap<CleaningResult>(res)
}

export async function cleanOutlier(projectId: string, datasetId: string, body: CleanOutlierRequest) {
  const res = await api.post(`/projects/${projectId}/datasets/${datasetId}/clean/outlier`, body)
  return unwrap<CleaningResult>(res)
}

export async function cleanDedup(projectId: string, datasetId: string, body: CleanDedupRequest) {
  const res = await api.post(`/projects/${projectId}/datasets/${datasetId}/clean/dedup`, body)
  return unwrap<CleaningResult>(res)
}

export async function cleanEncode(projectId: string, datasetId: string, body: CleanEncodeRequest) {
  const res = await api.post(`/projects/${projectId}/datasets/${datasetId}/clean/encode`, body)
  return unwrap<CleaningResult>(res)
}

export async function cleanTypeConvert(projectId: string, datasetId: string, body: CleanTypeConvertRequest) {
  const res = await api.post(`/projects/${projectId}/datasets/${datasetId}/clean/type-convert`, body)
  return unwrap<CleaningResult>(res)
}

export async function runEda(projectId: string, datasetId: string, body: EDARequest) {
  const res = await api.post(`/projects/${projectId}/datasets/${datasetId}/eda`, body)
  return unwrap<EDAReport>(res)
}

export async function getEdaReport(projectId: string, datasetId: string) {
  const res = await api.get(`/projects/${projectId}/datasets/${datasetId}/eda/report`)
  return unwrap<EDAReport>(res)
}

export async function augmentDataset(projectId: string, datasetId: string, body: AugmentRequest) {
  const res = await api.post(`/projects/${projectId}/datasets/${datasetId}/augment`, body)
  return unwrap<AugmentResult>(res)
}
