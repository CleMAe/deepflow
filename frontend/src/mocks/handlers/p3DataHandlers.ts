import { http, HttpResponse } from 'msw'
import type { components } from '@/api/types'

type Dataset = components['schemas']['Dataset']
type UploadInitRequest = components['schemas']['UploadInitRequest']

interface UploadState {
  projectId: string
  filename: string
  totalChunks: number
  receivedChunks: number[]
  datasetName?: string
  format?: Dataset['format']
}

const mockDatasets: Dataset[] = [
  {
    id: 'ds-1',
    project_id: 'proj-1',
    name: 'train_images_v1',
    format: 'image',
    file_path: '/projects/proj-1/datasets/ds-1',
    num_samples: 5000,
    num_columns: 3,
    tags: ['train', 'cv'],
    status: 'ready',
    size_bytes: 512_000_000,
    created_at: '2026-05-18T10:00:00Z',
    updated_at: '2026-05-18T10:00:00Z',
  },
  {
    id: 'ds-2',
    project_id: 'proj-1',
    name: 'product_labels',
    format: 'csv',
    file_path: '/projects/proj-1/datasets/ds-2',
    num_samples: 12000,
    num_columns: 8,
    tags: ['labels'],
    status: 'ready',
    size_bytes: 4_800_000,
    created_at: '2026-05-18T11:00:00Z',
    updated_at: '2026-05-18T11:30:00Z',
  },
  {
    id: 'ds-3',
    project_id: 'proj-2',
    name: 'sales_data_2025',
    format: 'csv',
    file_path: '/projects/proj-2/datasets/ds-3',
    num_samples: 8500,
    num_columns: 12,
    tags: ['regression'],
    status: 'cleaned',
    size_bytes: 2_100_000,
    created_at: '2026-05-18T09:00:00Z',
    updated_at: '2026-05-18T14:00:00Z',
  },
  {
    id: 'ds-4',
    project_id: 'proj-2',
    name: 'customer_events',
    format: 'json',
    file_path: '/projects/proj-2/datasets/ds-4',
    num_samples: 3200,
    num_columns: 6,
    tags: ['events'],
    status: 'uploading',
    size_bytes: 980_000,
    created_at: '2026-05-19T08:00:00Z',
    updated_at: '2026-05-19T08:00:00Z',
  },
]

const uploadSessions = new Map<string, UploadState>()

function newId(prefix: string) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
}

function recommendedChunkSize(format?: Dataset['format']) {
  switch (format) {
    case 'csv':
      return 512 * 1024
    case 'json':
      return 1024 * 1024
    case 'image':
      return 4 * 1024 * 1024
    default:
      return 2 * 1024 * 1024
  }
}

function inferFormat(filename: string, hint?: UploadInitRequest['format']): Dataset['format'] {
  if (hint) return hint
  const lower = filename.toLowerCase()
  if (lower.endsWith('.csv')) return 'csv'
  if (lower.endsWith('.json') || lower.endsWith('.jsonl')) return 'json'
  if (/\.(png|jpe?g|gif|webp|bmp)$/.test(lower)) return 'image'
  return 'other'
}

function filterDatasets(
  projectId: string,
  search?: string | null,
  format?: string | null,
  status?: string | null,
) {
  return mockDatasets.filter((dataset) => {
    if (dataset.project_id !== projectId) return false
    if (format && dataset.format !== format) return false
    if (status && dataset.status !== status) return false
    if (search) {
      const keyword = search.toLowerCase()
      const inName = dataset.name?.toLowerCase().includes(keyword)
      const inTags = dataset.tags?.some((tag) => tag.toLowerCase().includes(keyword))
      if (!inName && !inTags) return false
    }
    return true
  })
}

function paginate<T>(items: T[], page: number, pageSize: number) {
  const start = (page - 1) * pageSize
  return items.slice(start, start + pageSize)
}

export const p3DataHandlers = [
  http.get('/api/v1/projects/:projectId/datasets', ({ params, request }) => {
    const url = new URL(request.url)
    const page = Number(url.searchParams.get('page') || 1)
    const pageSize = Number(url.searchParams.get('page_size') || 20)
    const search = url.searchParams.get('search')
    const format = url.searchParams.get('format')
    const status = url.searchParams.get('status')

    const filtered = filterDatasets(params.projectId as string, search, format, status)
    const items = paginate(filtered, page, pageSize)

    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        page,
        page_size: pageSize,
        total: filtered.length,
        items,
      },
      request_id: `mock-p3-list-${Date.now()}`,
    })
  }),

  http.post('/api/v1/projects/:projectId/datasets/upload/init', async ({ params, request }) => {
    const body = (await request.json()) as UploadInitRequest
    const uploadId = newId('upload')

    const format = inferFormat(body.filename, body.format)

    uploadSessions.set(uploadId, {
      projectId: params.projectId as string,
      filename: body.filename,
      totalChunks: body.total_chunks,
      receivedChunks: [],
      datasetName: body.dataset_name,
      format,
    })

    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        upload_id: uploadId,
        chunk_size: recommendedChunkSize(format),
        received_chunks: [],
      },
      request_id: `mock-p3-init-${uploadId}`,
    })
  }),

  http.post(
    '/api/v1/projects/:projectId/datasets/upload/:uploadId/chunk',
    async ({ params, request }) => {
      const uploadId = params.uploadId as string
      const session = uploadSessions.get(uploadId)
      if (!session) {
        return HttpResponse.json(
          { code: 30_02_001, message: 'upload session not found', data: null, request_id: 'mock-p3-err' },
          { status: 404 },
        )
      }

      session.projectId = params.projectId as string
      const formData = await request.formData()
      const chunkIndex = Number(formData.get('chunk_index') ?? 0)
      if (!session.receivedChunks.includes(chunkIndex)) {
        session.receivedChunks.push(chunkIndex)
      }

      return HttpResponse.json({
        code: 0,
        message: 'success',
        data: { received_chunks: [...session.receivedChunks].sort((a, b) => a - b) },
        request_id: `mock-p3-chunk-${uploadId}-${chunkIndex}`,
      })
    },
  ),

  http.post(
    '/api/v1/projects/:projectId/datasets/upload/:uploadId/complete',
    async ({ params, request }) => {
      const uploadId = params.uploadId as string
      const session = uploadSessions.get(uploadId)
      if (!session) {
        return HttpResponse.json(
          { code: 30_02_001, message: 'upload session not found', data: null, request_id: 'mock-p3-err' },
          { status: 404 },
        )
      }

      const body = (await request.json()) as {
        total_chunks: number
        dataset_name?: string
        tags?: string[]
      }

      const dataset: Dataset = {
        id: newId('ds'),
        project_id: params.projectId as string,
        name: body.dataset_name || session.datasetName || session.filename.replace(/\.[^.]+$/, ''),
        format: session.format,
        file_path: `/projects/${params.projectId}/datasets/${uploadId}`,
        num_samples: Math.floor(Math.random() * 5000) + 100,
        num_columns: session.format === 'image' ? 3 : 8,
        tags: body.tags ?? ['uploaded'],
        status: 'ready',
        size_bytes: session.totalChunks * 1024 * 256,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      mockDatasets.unshift(dataset)
      uploadSessions.delete(uploadId)

      return HttpResponse.json({
        code: 0,
        message: 'success',
        data: dataset,
        request_id: `mock-p3-complete-${uploadId}`,
      })
    },
  ),
]
