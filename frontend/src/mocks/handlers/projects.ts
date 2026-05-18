import { http, HttpResponse } from 'msw'

const mockProjects = [
  {
    id: 'proj-1',
    name: '商品图像分类',
    description: '电商商品图像分类项目',
    owner_id: 'mock-user-id',
    created_at: '2026-05-18T08:00:00Z',
  },
  {
    id: 'proj-2',
    name: '销售预测',
    description: '基于历史数据的销售回归预测',
    owner_id: 'mock-user-id',
    created_at: '2026-05-18T09:00:00Z',
  },
]

export const projectHandlers = [
  http.get('/api/v1/projects', () => {
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        page: 1,
        page_size: 20,
        total: mockProjects.length,
        items: mockProjects,
      },
      request_id: 'mock-req-5',
    })
  }),

  http.get('/api/v1/projects/:id', ({ params }) => {
    const project = mockProjects.find((p) => p.id === params.id)
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: project || mockProjects[0],
      request_id: 'mock-req-6',
    })
  }),

  http.post('/api/v1/projects', async () => {
    return HttpResponse.json(
      {
        code: 0,
        message: 'success',
        data: {
          id: 'proj-new',
          name: '新项目',
          description: '',
          owner_id: 'mock-user-id',
          created_at: new Date().toISOString(),
        },
        request_id: 'mock-req-7',
      },
      { status: 201 }
    )
  }),
]
