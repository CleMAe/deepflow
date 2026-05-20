import { http, HttpResponse } from 'msw'
import type { components } from '@/api/types'

import { DEMO_PROJECT_ID, MOCK_ALT_PROJECT_ID } from '@/mocks/demoIds'

type Experiment = components['schemas']['Experiment']

const mockExperiments: Experiment[] = [
  {
    id: 'exp-1',
    project_id: MOCK_ALT_PROJECT_ID,
    job_id: 'job-1',
    name: 'ResNet-18 基准实验',
    metrics: { accuracy: 0.92, precision: 0.91, recall: 0.89, f1: 0.9 },
    params_snap: { epochs: 10, batch_size: 32, learning_rate: 0.001, optimizer: 'adam' },
    tags: ['baseline', 'resnet'],
    notes: '第一轮基准训练，效果良好',
    created_at: '2026-05-19T08:30:00Z',
  },
  {
    id: 'exp-2',
    project_id: DEMO_PROJECT_ID,
    job_id: 'job-2',
    name: 'MLP 销售预测实验',
    metrics: { mse: 0.18, rmse: 0.42, mae: 0.31 },
    params_snap: { epochs: 50, batch_size: 64, learning_rate: 0.01, optimizer: 'adam' },
    tags: ['mlp', 'regression'],
    notes: '使用 Adam 优化器，收敛较慢',
    created_at: '2026-05-20T09:10:00Z',
  },
]

export const experimentHandlers = [
  http.get('/api/v1/projects/:projectId/experiments', ({ params }) => {
    const items = mockExperiments.filter((e) => e.project_id === params.projectId)
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: { page: 1, page_size: 20, total: items.length, items },
      request_id: 'mock-experiments-list',
    })
  }),

  http.post('/api/v1/projects/:projectId/experiments', async ({ request, params }) => {
    const body = (await request.json()) as { name: string; job_id: string; tags?: string[]; notes?: string }
    const newExp: Experiment = {
      id: `exp-${Math.random().toString(36).slice(2)}`,
      project_id: params.projectId as string,
      job_id: body.job_id,
      name: body.name,
      metrics: {},
      params_snap: {},
      tags: body.tags ?? [],
      notes: body.notes ?? '',
      created_at: new Date().toISOString(),
    }
    mockExperiments.push(newExp)
    return HttpResponse.json(
      { code: 0, message: 'success', data: newExp, request_id: 'mock-experiments-create' },
      { status: 201 }
    )
  }),

  http.get('/api/v1/projects/:projectId/experiments/:expId', ({ params }) => {
    const exp = mockExperiments.find((e) => e.id === params.expId)
    if (!exp) {
      return HttpResponse.json({ code: 40020001, message: 'experiment not found' }, { status: 404 })
    }
    return HttpResponse.json({ code: 0, message: 'success', data: exp, request_id: 'mock-experiments-get' })
  }),

  http.post('/api/v1/projects/:projectId/experiments/compare', async ({ request }) => {
    const body = (await request.json()) as { experiment_ids: string[] }
    const selected = mockExperiments.filter((e) => body.experiment_ids.includes(e.id!))
    const metricComparison: Record<string, number[]> = {}
    selected.forEach((exp) => {
      Object.entries(exp.metrics ?? {}).forEach(([key, val]) => {
        if (typeof val === 'number') {
          if (!metricComparison[key]) metricComparison[key] = []
          metricComparison[key].push(val)
        }
      })
    })
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: { experiments: selected, metric_comparison: metricComparison, param_diff: {} },
      request_id: 'mock-experiments-compare',
    })
  }),
]
