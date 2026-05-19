import api, { type ApiResponse } from '@/lib/axios'
import type { components } from '@/api/types'

export type Dataset = components['schemas']['Dataset']
export type PaginatedDatasets = components['schemas']['PaginatedDatasets']
export type UploadInitRequest = components['schemas']['UploadInitRequest']
export type UploadSession = components['schemas']['UploadSession']

export interface ListDatasetsParams {
  page?: number
  page_size?: number
  format?: Dataset['format']
  status?: Dataset['status']
  search?: string
}

function unwrapApiData<T>(res: unknown) {
  return (res as ApiResponse<T>).data
}

export async function listDatasets(projectId: string, params?: ListDatasetsParams) {
  const res = await api.get(`/projects/${projectId}/datasets`, { params })
  return unwrapApiData<PaginatedDatasets>(res)
}

export async function initDatasetUpload(projectId: string, payload: UploadInitRequest) {
  const res = await api.post(`/projects/${projectId}/datasets/upload/init`, payload)
  return unwrapApiData<UploadSession>(res)
}

export async function uploadDatasetChunk(
  projectId: string,
  uploadId: string,
  formData: FormData,
) {
  const res = await api.post(
    `/projects/${projectId}/datasets/upload/${uploadId}/chunk`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return unwrapApiData<{ received_chunks?: number[] }>(res)
}

export async function completeDatasetUpload(
  projectId: string,
  uploadId: string,
  payload: { total_chunks: number; dataset_name?: string; tags?: string[] },
) {
  const res = await api.post(
    `/projects/${projectId}/datasets/upload/${uploadId}/complete`,
    payload,
  )
  return unwrapApiData<Dataset>(res)
}
