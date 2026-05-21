import { http, HttpResponse } from 'msw'
import type { components } from '@/api/types'

import { DEMO_DATASET_IMAGE_ID } from '@/mocks/demoIds'

type Dataset = components['schemas']['Dataset']

const labelStore = new Map<string, string[]>()

function previewForDataset(ds: Dataset | undefined) {
  if (!ds) {
    return {
      columns: ['col_a', 'col_b'],
      rows: [{ col_a: '—', col_b: '—' }],
      total_rows: 0,
    }
  }
  if (ds.format === 'image') {
    return {
      columns: ['image_id', 'filename', 'labels'],
      rows: [
        { image_id: 'img-001', filename: 'sample_001.jpg', labels: 'cat' },
        { image_id: 'img-002', filename: 'sample_002.jpg', labels: 'dog' },
      ],
      total_rows: ds.num_samples ?? 2,
    }
  }
  return {
    columns: ['date', 'region', 'sales'],
    rows: [
      { date: '2025-01-01', region: '华东', sales: 1280 },
      { date: '2025-01-02', region: '华北', sales: 980 },
      { date: '2025-01-03', region: '华南', sales: 1420 },
    ],
    total_rows: ds.num_samples ?? 3,
  }
}

function mockImages(datasetId: string, page: number, pageSize: number) {
  const total = 24
  const start = (page - 1) * pageSize
  const items = Array.from({ length: Math.min(pageSize, total - start) }, (_, i) => {
    const idx = start + i + 1
    const id = `${datasetId}-img-${String(idx).padStart(3, '0')}`
    const stored = labelStore.get(id)
    return {
      id,
      filename: `item_${idx}.jpg`,
      thumbnail_path: `https://picsum.photos/seed/${datasetId}${idx}/120/120`,
      labels: stored ?? (idx % 3 === 0 ? ['positive'] : ['negative']),
      width: 224,
      height: 224,
    }
  })
  return { page, page_size: pageSize, total, items }
}

export const p3Day2Handlers = [
  http.get('/api/v1/projects/:projectId/datasets/:dsId/preview', ({ params }) => {
    const dsId = params.dsId as string
    const format: Dataset['format'] = dsId === DEMO_DATASET_IMAGE_ID ? 'image' : 'csv'
    const mockDs: Dataset = {
      id: dsId,
      name: 'mock',
      format,
      num_samples: 100,
    }
    const data = previewForDataset(mockDs)
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data,
      request_id: `mock-p3-preview-${dsId}`,
    })
  }),

  http.get('/api/v1/projects/:projectId/datasets/:dsId/images', ({ params, request }) => {
    const url = new URL(request.url)
    const page = Number(url.searchParams.get('page') || 1)
    const pageSize = Number(url.searchParams.get('page_size') || 12)
    const label = url.searchParams.get('label')
    const dsId = params.dsId as string
    let data = mockImages(dsId, page, pageSize)
    if (label) {
      data = {
        ...data,
        items: data.items.filter((item) => (item.labels ?? []).includes(label)),
        total: data.items.filter((item) => (item.labels ?? []).includes(label)).length,
      }
    }
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data,
      request_id: `mock-p3-images-${dsId}`,
    })
  }),

  http.put('/api/v1/projects/:projectId/datasets/:dsId/labels', async ({ request }) => {
    const body = (await request.json()) as components['schemas']['BatchLabelUpdate']
    for (const item of body.items) {
      labelStore.set(item.image_id, item.labels)
    }
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: { updated: body.items.length },
      request_id: 'mock-p3-labels',
    })
  }),
]
