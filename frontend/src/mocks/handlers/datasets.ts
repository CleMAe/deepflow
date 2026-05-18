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
]
