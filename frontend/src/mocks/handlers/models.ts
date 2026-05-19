import { http, HttpResponse } from 'msw'
import type { components } from '@/api/types'
import {
  getProjectModels,
  libraryModels,
  projectModels,
} from '../fixtures/models'

type ModelCreate = components['schemas']['ModelCreate']
type ModelUpdate = components['schemas']['ModelUpdate']
type ModelValidateRequest = components['schemas']['ModelValidateRequest']

function apiOk<T>(data: T, requestId = 'mock-p4-models') {
  return HttpResponse.json({
    code: 0,
    message: 'success',
    data,
    request_id: requestId,
  })
}

function filterLibrary(taskType: string | null, search: string | null) {
  let items = [...libraryModels]
  if (taskType) {
    items = items.filter((m) => m.task_type === taskType)
  }
  if (search) {
    const q = search.toLowerCase()
    items = items.filter(
      (m) =>
        m.name?.toLowerCase().includes(q) ||
        m.arch_type?.toLowerCase().includes(q) ||
        m.description?.toLowerCase().includes(q)
    )
  }
  return items
}

export const modelsHandlers = [
  http.get('/api/v1/models/library', ({ request }) => {
    const url = new URL(request.url)
    const taskType = url.searchParams.get('task_type')
    const search = url.searchParams.get('search')
    return apiOk(filterLibrary(taskType, search))
  }),

  http.get('/api/v1/models/library/:modelId', ({ params }) => {
    const model = libraryModels.find((m) => m.model_id === params.modelId)
    if (!model) {
      return HttpResponse.json(
        { code: 40400101, message: 'Model not found in library', data: null, request_id: 'mock-p4-404' },
        { status: 404 }
      )
    }
    return apiOk(model)
  }),

  http.get('/api/v1/projects/:projectId/models', ({ params, request }) => {
    const url = new URL(request.url)
    const page = Number(url.searchParams.get('page') || 1)
    const pageSize = Number(url.searchParams.get('page_size') || 20)
    const items = getProjectModels(String(params.projectId))

    return apiOk({
      page,
      page_size: pageSize,
      total: items.length,
      items,
    })
  }),

  http.post('/api/v1/projects/:projectId/models', async ({ params, request }) => {
    const payload = (await request.json()) as ModelCreate
    const now = new Date().toISOString()
    const library = libraryModels.find((m) => m.arch_type === payload.arch_type)
    const created = {
      id: `model-${Date.now()}`,
      project_id: String(params.projectId),
      name: payload.name,
      arch_type: payload.arch_type,
      params_cfg: payload.params_cfg ?? library?.default_hyperparams ?? {},
      pretrained: library?.pretrained_available ?? false,
      description: payload.description ?? library?.description,
      created_at: now,
      updated_at: now,
    }
    projectModels.push(created)
    return HttpResponse.json(
      {
        code: 0,
        message: 'success',
        data: created,
        request_id: 'mock-p4-create',
      },
      { status: 201 }
    )
  }),

  http.get('/api/v1/projects/:projectId/models/:mId', ({ params }) => {
    const model = projectModels.find(
      (m) => m.id === params.mId && m.project_id === params.projectId
    )
    if (!model) {
      return HttpResponse.json(
        { code: 40400201, message: 'Project model not found', data: null, request_id: 'mock-p4-404' },
        { status: 404 }
      )
    }
    return apiOk(model)
  }),

  http.put('/api/v1/projects/:projectId/models/:mId', async ({ params, request }) => {
    const payload = (await request.json()) as ModelUpdate
    const index = projectModels.findIndex(
      (m) => m.id === params.mId && m.project_id === params.projectId
    )
    if (index < 0) {
      return HttpResponse.json(
        { code: 40400201, message: 'Project model not found', data: null, request_id: 'mock-p4-404' },
        { status: 404 }
      )
    }
    const current = projectModels[index]
    const updated = {
      ...current,
      ...payload,
      params_cfg: payload.params_cfg ?? current.params_cfg,
      updated_at: new Date().toISOString(),
    }
    projectModels[index] = updated
    return apiOk(updated)
  }),

  http.post('/api/v1/projects/:projectId/models/:mId/validate', async ({ request }) => {
    const payload = (await request.json()) as ModelValidateRequest
    const cfg = payload.params_cfg ?? {}
    const errors: { field: string; message: string }[] = []
    const warnings: { field: string; message: string }[] = []

    if (cfg.num_classes !== undefined && Number(cfg.num_classes) < 2) {
      errors.push({ field: 'num_classes', message: '分类任务至少需要 2 个类别' })
    }
    if (cfg.learning_rate !== undefined && Number(cfg.learning_rate) <= 0) {
      errors.push({ field: 'learning_rate', message: '学习率必须大于 0' })
    }
    if (cfg.batch_size !== undefined && Number(cfg.batch_size) < 1) {
      errors.push({ field: 'batch_size', message: 'Batch Size 至少为 1' })
    }
    if (cfg.epochs !== undefined && Number(cfg.epochs) > 200) {
      warnings.push({ field: 'epochs', message: '训练轮数较大，可能耗时较长' })
    }

    return apiOk({
      valid: errors.length === 0,
      errors,
      warnings,
    })
  }),
]
