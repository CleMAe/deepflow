import { http, HttpResponse } from 'msw'

import {
  DEMO_DATASET_CSV_ID,
  DEMO_DATASET_IMAGE_ID,
  DEMO_PROJECT_ID,
  MOCK_ALT_PROJECT_ID,
} from '@/mocks/demoIds'

const mockDatasets = [
  {
    id: DEMO_DATASET_IMAGE_ID,
    name: 'train_images_v1',
    project_id: MOCK_ALT_PROJECT_ID,
    format: 'image',
    file_path: `/projects/${MOCK_ALT_PROJECT_ID}/datasets/${DEMO_DATASET_IMAGE_ID}`,
    num_samples: 5000,
    status: 'ready',
    created_at: '2026-05-18T10:00:00Z',
  },
  {
    id: DEMO_DATASET_CSV_ID,
    name: 'sales_data_2025',
    project_id: DEMO_PROJECT_ID,
    format: 'csv',
    file_path: `/projects/${DEMO_PROJECT_ID}/datasets/${DEMO_DATASET_CSV_ID}`,
    num_samples: 12000,
    status: 'ready',
    created_at: '2026-05-18T11:00:00Z',
  },
]

const uploadSessions = new Map<string, { received_chunks: number[]; total_chunks: number }>()

export const datasetHandlers = [
  http.get('/api/v1/projects/:projectId/datasets', ({ params }) => {
    const projectId = params.projectId as string
    const items = mockDatasets.filter((d) => d.project_id === projectId)
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        page: 1,
        page_size: 20,
        total: items.length,
        items,
      },
      request_id: 'mock-req-8',
    })
  }),

  http.get('/api/v1/projects/:projectId/datasets/:dsId', ({ params }) => {
    const ds = mockDatasets.find((d) => d.id === params.dsId)
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: ds || mockDatasets[0],
      request_id: 'mock-req-9',
    })
  }),

  http.post('/api/v1/projects/:projectId/datasets/upload/init', async ({ request }) => {
    const body = (await request.json()) as { filename: string; total_chunks: number }
    const uploadId = `upload-${Math.random().toString(36).slice(2)}`
    uploadSessions.set(uploadId, { received_chunks: [], total_chunks: body.total_chunks })
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: { upload_id: uploadId, chunk_size: 5 * 1024 * 1024, received_chunks: [] },
      request_id: 'mock-req-upload-init',
    })
  }),

  http.post('/api/v1/projects/:projectId/datasets/upload/:uploadId/chunk', async ({ params, request }) => {
    const session = uploadSessions.get(params.uploadId as string)
    if (!session) {
      return HttpResponse.json({ code: 30020002, message: 'Upload session not found' }, { status: 404 })
    }
    const form = await request.formData()
    const index = Number(form.get('chunk_index'))
    if (!session.received_chunks.includes(index)) {
      session.received_chunks.push(index)
    }
    return HttpResponse.json({
      code: 0,
      message: 'chunk received',
      data: { received_chunks: session.received_chunks },
      request_id: 'mock-req-chunk',
    })
  }),

  http.put('/api/v1/projects/:projectId/datasets/:dsId', async ({ params, request }) => {
    const body = (await request.json()) as { name?: string; tags?: string[] }
    const idx = mockDatasets.findIndex((d) => d.id === params.dsId)
    if (idx < 0) {
      return HttpResponse.json({ code: 30020001, message: 'Dataset not found' }, { status: 404 })
    }
    mockDatasets[idx] = { ...mockDatasets[idx], ...body }
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: mockDatasets[idx],
      request_id: 'mock-req-update-ds',
    })
  }),

  http.delete('/api/v1/projects/:projectId/datasets/:dsId', ({ params }) => {
    const idx = mockDatasets.findIndex((d) => d.id === params.dsId)
    if (idx < 0) {
      return HttpResponse.json({ code: 30020001, message: 'Dataset not found' }, { status: 404 })
    }
    mockDatasets.splice(idx, 1)
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: { dataset_id: params.dsId },
      request_id: 'mock-req-delete-ds',
    })
  }),

  http.post('/api/v1/projects/:projectId/datasets/upload/:uploadId/complete', async ({ params, request }) => {
    const session = uploadSessions.get(params.uploadId as string)
    if (!session) {
      return HttpResponse.json({ code: 30020002, message: 'Upload session not found' }, { status: 404 })
    }
    const body = (await request.json()) as { dataset_name?: string }
    uploadSessions.delete(params.uploadId as string)
    const newId = globalThis.crypto?.randomUUID?.() ?? `00000000-0000-4000-8000-${Date.now().toString(16).padStart(12, '0').slice(0, 12)}`
    const newDs = {
      id: newId,
      name: body.dataset_name || 'uploaded_dataset',
      project_id: String(params.projectId),
      format: 'csv',
      file_path: `/projects/${params.projectId}/datasets/new`,
      num_samples: 0,
      status: 'ready',
      created_at: new Date().toISOString(),
    }
    mockDatasets.push(newDs)
    return HttpResponse.json({
      code: 0,
      message: 'upload completed',
      data: newDs,
      request_id: 'mock-req-complete',
    })
  }),

]
