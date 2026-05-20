import { http, HttpResponse } from 'msw'

const mockModels = [
  {
    id: 'model-1',
    project_id: 'proj-1',
    name: 'ResNet-18 商品分类',
    arch_type: 'resnet18',
    params_cfg: { num_classes: 3, image_size: 224 },
    pretrained: true,
    pretrained_source: 'huggingface',
    model_path: '/projects/proj-1/models/model-1/checkpoint/best.pth',
    description: '用于商品图片分类的默认模型',
    created_at: '2026-05-18T12:00:00Z',
    updated_at: '2026-05-18T12:00:00Z',
  },
  {
    id: 'model-2',
    project_id: 'proj-1',
    name: 'MLP 销售预测',
    arch_type: 'mlp',
    params_cfg: { hidden_dims: [128, 64], output_dim: 1 },
    pretrained: false,
    model_path: '/projects/proj-1/models/model-2/checkpoint/latest.pth',
    description: '用于结构化业务数据回归预测',
    created_at: '2026-05-18T12:30:00Z',
    updated_at: '2026-05-18T12:30:00Z',
  },
]

export const modelHandlers = [
  http.get('/api/v1/projects/:projectId/models', ({ params }) => {
    const items = mockModels.filter((m) => m.project_id === params.projectId)
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: { page: 1, page_size: 20, total: items.length, items },
      request_id: 'mock-models-list',
    })
  }),

  http.post('/api/v1/projects/:projectId/models', async ({ request, params }) => {
    const body = (await request.json()) as {
      name: string
      arch_type: string
      params_cfg?: Record<string, unknown>
      description?: string
    }
    const newModel = {
      id: `model-${Math.random().toString(36).slice(2)}`,
      project_id: params.projectId,
      name: body.name,
      arch_type: body.arch_type,
      params_cfg: body.params_cfg ?? {},
      pretrained: false,
      model_path: '',
      description: body.description ?? '',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    mockModels.push(newModel)
    return HttpResponse.json(
      { code: 0, message: 'success', data: newModel, request_id: 'mock-models-create' },
      { status: 201 }
    )
  }),

  http.get('/api/v1/projects/:projectId/models/:mId', ({ params }) => {
    const model = mockModels.find((m) => m.id === params.mId)
    if (!model) {
      return HttpResponse.json({ code: 40020001, message: 'model not found' }, { status: 404 })
    }
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: model,
      request_id: 'mock-models-get',
    })
  }),

  http.put('/api/v1/projects/:projectId/models/:mId', async ({ params, request }) => {
    const model = mockModels.find((m) => m.id === params.mId)
    if (!model) {
      return HttpResponse.json({ code: 40020001, message: 'model not found' }, { status: 404 })
    }
    const body = (await request.json()) as { name?: string; params_cfg?: Record<string, unknown>; description?: string }
    Object.assign(model, body, { updated_at: new Date().toISOString() })
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: model,
      request_id: 'mock-models-update',
    })
  }),

  http.delete('/api/v1/projects/:projectId/models/:mId', ({ params }) => {
    const idx = mockModels.findIndex((m) => m.id === params.mId)
    if (idx === -1) {
      return HttpResponse.json({ code: 40020001, message: 'model not found' }, { status: 404 })
    }
    mockModels.splice(idx, 1)
    return HttpResponse.json({ code: 0, message: 'deleted', data: null, request_id: 'mock-models-delete' })
  }),

  http.post('/api/v1/projects/:projectId/models/:mId/validate', async ({ request }) => {
    const body = (await request.json()) as { params_cfg?: Record<string, unknown> }
    const cfg = body.params_cfg ?? {}
    const errors: { field: string; message: string }[] = []
    if (cfg.num_classes !== undefined && typeof cfg.num_classes !== 'number') {
      errors.push({ field: 'num_classes', message: 'must be a number' })
    }
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: { valid: errors.length === 0, errors, warnings: [] },
      request_id: 'mock-models-validate',
    })
  }),

  http.post('/api/v1/projects/:projectId/models/:mId/pretrained', async ({ params }) => {
    const model = mockModels.find((m) => m.id === params.mId)
    if (!model) {
      return HttpResponse.json({ code: 40020001, message: 'model not found' }, { status: 404 })
    }
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: { status: 'ready', model_path: `/projects/${params.projectId}/models/${params.mId}/pretrained.pth` },
      request_id: 'mock-models-pretrained',
    })
  }),
]
