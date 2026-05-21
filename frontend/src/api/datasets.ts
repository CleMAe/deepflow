import api, { type ApiResponse } from '@/lib/axios'
import type { components } from '@/api/types'

export type Dataset = components['schemas']['Dataset']
export type PaginatedDatasets = components['schemas']['PaginatedDatasets']
export type DatasetPreview = components['schemas']['DatasetPreview']
export type PaginatedImages = components['schemas']['PaginatedImages']
export type BatchLabelUpdate = components['schemas']['BatchLabelUpdate']
export type ImageItem = components['schemas']['ImageItem']
export type DatasetUpdate = components['schemas']['DatasetUpdate']

function unwrap<T>(res: unknown): T {
  return (res as ApiResponse<T>).data as T
}

export async function listDatasets(
  projectId: string,
  params?: { page?: number; page_size?: number; search?: string; format?: string; status?: string },
) {
  const res = await api.get(`/projects/${projectId}/datasets`, { params })
  return unwrap<PaginatedDatasets>(res)
}

export async function updateDataset(projectId: string, datasetId: string, body: DatasetUpdate) {
  const res = await api.put(`/projects/${projectId}/datasets/${datasetId}`, body)
  return unwrap<Dataset>(res)
}

export async function deleteDataset(projectId: string, datasetId: string) {
  const res = await api.delete(`/projects/${projectId}/datasets/${datasetId}`)
  return unwrap<{ dataset_id?: string }>(res)
}

export async function getDatasetPreview(projectId: string, datasetId: string) {
  const res = await api.get(`/projects/${projectId}/datasets/${datasetId}/preview`)
  return unwrap<DatasetPreview>(res)
}

export async function listDatasetImages(
  projectId: string,
  datasetId: string,
  params?: { page?: number; page_size?: number; label?: string },
) {
  const res = await api.get(`/projects/${projectId}/datasets/${datasetId}/images`, { params })
  return unwrap<PaginatedImages>(res)
}

export async function updateDatasetLabels(
  projectId: string,
  datasetId: string,
  payload: BatchLabelUpdate,
) {
  const res = await api.put(`/projects/${projectId}/datasets/${datasetId}/labels`, payload)
  return unwrap<{ updated?: number }>(res)
}
