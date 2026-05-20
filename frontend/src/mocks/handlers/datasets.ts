import { http, HttpResponse } from 'msw'

const mockDatasets = [
  {
    id: 'ds-1',
    name: 'train_images_v1',
    project_id: 'proj-1',
    format: 'image',
    file_path: '/projects/proj-1/datasets/ds-1',
    num_samples: 5000,
    status: 'ready',
    created_at: '2026-05-18T10:00:00Z',
  },
  {
    id: 'ds-2',
    name: 'sales_data_2025',
    project_id: 'proj-2',
    format: 'csv',
    file_path: '/projects/proj-2/datasets/ds-2',
    num_samples: 12000,
    status: 'ready',
    created_at: '2026-05-18T11:00:00Z',
  },
]

const uploadSessions = new Map<string, { received_chunks: number[]; total_chunks: number }>()

export const datasetHandlers = [
  http.get('/api/v1/projects/:projectId/datasets', () => {
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        page: 1,
        page_size: 20,
        total: mockDatasets.length,
        items: mockDatasets,
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

  http.post('/api/v1/projects/:projectId/datasets/upload/:uploadId/chunk', async ({ params }) => {
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

  http.post('/api/v1/projects/:projectId/datasets/upload/:uploadId/complete', async ({ params, request }) => {
    const session = uploadSessions.get(params.uploadId as string)
    if (!session) {
      return HttpResponse.json({ code: 30020002, message: 'Upload session not found' }, { status: 404 })
    }
    const body = (await request.json()) as { dataset_name?: string }
    uploadSessions.delete(params.uploadId as string)
    const newDs = {
      id: `ds-${Math.random().toString(36).slice(2)}`,
      name: body.dataset_name || 'uploaded_dataset',
      project_id: params.projectId,
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
