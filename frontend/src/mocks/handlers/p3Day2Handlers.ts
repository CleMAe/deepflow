import { http, HttpResponse } from 'msw'
import type { components } from '@/api/types'

const labelStore = new Map<string, string[]>()

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
  http.get('/api/v1/projects/:projectId/datasets/:dsId/images', ({ params, request }) => {
    const url = new URL(request.url)
    const page = Number(url.searchParams.get('page') || 1)
    const pageSize = Number(url.searchParams.get('page_size') || 12)
    const dsId = params.dsId as string
    const data = mockImages(dsId, page, pageSize)
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
