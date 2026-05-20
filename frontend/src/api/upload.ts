import api, { type ApiResponse } from '@/lib/axios'
import type { components } from '@/api/types'

export type UploadInitRequest = components['schemas']['UploadInitRequest']
export type UploadSession = components['schemas']['UploadSession']
export type Dataset = components['schemas']['Dataset']

function unwrapApiData<T>(res: unknown) {
  return (res as ApiResponse<T>).data
}

export async function initUpload(projectId: string, payload: UploadInitRequest) {
  const res = await api.post(`/projects/${projectId}/datasets/upload/init`, payload)
  return unwrapApiData<UploadSession>(res)
}

export async function uploadChunk(
  projectId: string,
  uploadId: string,
  chunkIndex: number,
  totalChunks: number,
  chunk: Blob,
) {
  const formData = new FormData()
  formData.append('chunk_index', String(chunkIndex))
  formData.append('total_chunks', String(totalChunks))
  formData.append('chunk', chunk)
  const res = await api.post(`/projects/${projectId}/datasets/upload/${uploadId}/chunk`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return unwrapApiData<{ received_chunks?: number[] }>(res)
}

export async function completeUpload(
  projectId: string,
  uploadId: string,
  payload: { total_chunks: number; dataset_name?: string; tags?: string[] },
) {
  const res = await api.post(`/projects/${projectId}/datasets/upload/${uploadId}/complete`, payload)
  return unwrapApiData<Dataset>(res)
}

export async function uploadSimple(projectId: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('name', file.name)
  const res = await api.post(`/projects/${projectId}/datasets/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return unwrapApiData<Dataset>(res)
}
