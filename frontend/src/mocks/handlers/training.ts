import { http, HttpResponse } from 'msw'
import type { components } from '@/api/types'

import { DEMO_DATASET_CSV_ID, DEMO_DATASET_IMAGE_ID, DEMO_PROJECT_ID, MOCK_ALT_PROJECT_ID } from '@/mocks/demoIds'

type TrainingStatus = components['schemas']['TrainingStatus']
type TrainingJob = components['schemas']['TrainingJob']

const mockJobs: TrainingJob[] = [
  {
    id: 'job-1',
    project_id: MOCK_ALT_PROJECT_ID,
    name: 'ResNet-18 第一轮训练',
    model_id: 'model-1',
    dataset_id: DEMO_DATASET_IMAGE_ID,
    val_dataset_id: DEMO_DATASET_IMAGE_ID,
    hyperparams: { epochs: 10, batch_size: 32, learning_rate: 0.001, optimizer: 'adam', loss_function: 'cross_entropy', weight_decay: 0, lr_scheduler: 'none', grad_accum_steps: 1, mixed_precision: false, checkpoint_every_n_epochs: 1 },
    status: 'success',
    device: 'cuda',
    current_epoch: 10,
    total_epochs: 10,
    metrics: { train_loss: 0.12, val_loss: 0.18, accuracy: 0.92, best_val_loss: 0.15, best_accuracy: 0.93 },
    checkpoint: `/projects/${MOCK_ALT_PROJECT_ID}/training/job-1/checkpoint/best.pth`,
    started_at: '2026-05-19T08:00:00Z',
    finished_at: '2026-05-19T08:30:00Z',
    created_at: '2026-05-19T07:55:00Z',
    updated_at: '2026-05-19T08:30:00Z',
  },
  {
    id: 'job-2',
    project_id: DEMO_PROJECT_ID,
    name: 'MLP 销售预测训练',
    model_id: 'model-2',
    dataset_id: DEMO_DATASET_CSV_ID,
    hyperparams: { epochs: 50, batch_size: 64, learning_rate: 0.01, optimizer: 'adam', loss_function: 'mse', weight_decay: 0.0001, lr_scheduler: 'step', grad_accum_steps: 1, mixed_precision: false, checkpoint_every_n_epochs: 5 },
    status: 'running',
    device: 'cpu',
    current_epoch: 12,
    total_epochs: 50,
    metrics: { train_loss: 0.34, val_loss: 0.41, accuracy: 0.78 },
    started_at: '2026-05-20T09:00:00Z',
    created_at: '2026-05-20T08:55:00Z',
    updated_at: '2026-05-20T09:10:00Z',
  },
]

const VALID_TRANSITIONS: Record<string, Set<string>> = {
  pending: new Set(['running', 'cancelled']),
  running: new Set(['paused', 'success', 'failed', 'cancelled']),
  paused: new Set(['running', 'cancelled']),
  success: new Set(),
  failed: new Set(),
  cancelled: new Set(),
}

function transition(status: TrainingStatus, action: 'start' | 'pause' | 'resume' | 'stop'): { status: TrainingStatus; error?: string } {
  const target: Record<string, TrainingStatus> = {
    start: 'running',
    pause: 'paused',
    resume: 'running',
    stop: 'cancelled',
  }
  const next = target[action]
  if (!VALID_TRANSITIONS[status]?.has(next)) {
    return { status, error: `Cannot transition from ${status} to ${next}` }
  }
  return { status: next }
}

export const trainingHandlers = [
  http.get('/api/v1/projects/:projectId/training-jobs', ({ params }) => {
    const items = mockJobs.filter((j) => j.project_id === params.projectId)
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: { page: 1, page_size: 20, total: items.length, items },
      request_id: 'mock-training-list',
    })
  }),

  http.post('/api/v1/projects/:projectId/training-jobs', async ({ request, params }) => {
    const body = (await request.json()) as {
      name: string
      model_id: string
      dataset_id: string
      val_dataset_id?: string
      hyperparams?: Record<string, unknown>
      device?: string
      description?: string
    }
    const newJob: TrainingJob = {
      id: `job-${Math.random().toString(36).slice(2)}`,
      project_id: params.projectId as string,
      name: body.name,
      model_id: body.model_id,
      dataset_id: body.dataset_id,
      val_dataset_id: body.val_dataset_id,
      hyperparams: body.hyperparams ?? {},
      status: 'pending',
      device: body.device ?? 'auto',
      current_epoch: 0,
      total_epochs: (body.hyperparams as { epochs?: number })?.epochs ?? 10,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    mockJobs.push(newJob)
    return HttpResponse.json(
      { code: 0, message: 'success', data: newJob, request_id: 'mock-training-create' },
      { status: 201 }
    )
  }),

  http.get('/api/v1/projects/:projectId/training-jobs/:jobId', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) {
      return HttpResponse.json({ code: 50020001, message: 'Training job not found' }, { status: 404 })
    }
    return HttpResponse.json({ code: 0, message: 'success', data: job, request_id: 'mock-training-get' })
  }),

  http.post('/api/v1/projects/:projectId/training-jobs/:jobId/start', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) return HttpResponse.json({ code: 50020001, message: 'Training job not found' }, { status: 404 })
    const result = transition(job.status!, 'start')
    if (result.error) {
      return HttpResponse.json({ code: 50010001, message: result.error }, { status: 400 })
    }
    job.status = result.status
    job.started_at = new Date().toISOString()
    job.updated_at = new Date().toISOString()
    return HttpResponse.json({ code: 0, message: 'success', data: job, request_id: 'mock-training-start' })
  }),

  http.post('/api/v1/projects/:projectId/training-jobs/:jobId/pause', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) return HttpResponse.json({ code: 50020001, message: 'Training job not found' }, { status: 404 })
    const result = transition(job.status!, 'pause')
    if (result.error) {
      return HttpResponse.json({ code: 50010001, message: result.error }, { status: 400 })
    }
    job.status = result.status
    job.updated_at = new Date().toISOString()
    return HttpResponse.json({ code: 0, message: 'success', data: job, request_id: 'mock-training-pause' })
  }),

  http.post('/api/v1/projects/:projectId/training-jobs/:jobId/resume', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) return HttpResponse.json({ code: 50020001, message: 'Training job not found' }, { status: 404 })
    const result = transition(job.status!, 'resume')
    if (result.error) {
      return HttpResponse.json({ code: 50010001, message: result.error }, { status: 400 })
    }
    job.status = result.status
    job.updated_at = new Date().toISOString()
    return HttpResponse.json({ code: 0, message: 'success', data: job, request_id: 'mock-training-resume' })
  }),

  http.post('/api/v1/projects/:projectId/training-jobs/:jobId/stop', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) return HttpResponse.json({ code: 50020001, message: 'Training job not found' }, { status: 404 })
    const result = transition(job.status!, 'stop')
    if (result.error) {
      return HttpResponse.json({ code: 50010001, message: result.error }, { status: 400 })
    }
    job.status = result.status
    job.finished_at = new Date().toISOString()
    job.updated_at = new Date().toISOString()
    return HttpResponse.json({ code: 0, message: 'success', data: job, request_id: 'mock-training-stop' })
  }),

  http.get('/api/v1/projects/:projectId/training-jobs/:jobId/logs', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) return HttpResponse.json({ code: 50020001, message: 'Training job not found' }, { status: 404 })
    const logs = [
      `INFO Training started at ${job.started_at || job.created_at}`,
      `INFO Epoch ${job.current_epoch}/${job.total_epochs} - loss: ${job.metrics?.train_loss ?? 0.5}`,
    ]
    return HttpResponse.json({ code: 0, message: 'success', data: { logs }, request_id: 'mock-training-logs' })
  }),

  http.get('/api/v1/projects/:projectId/training-jobs/:jobId/checkpoints', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) return HttpResponse.json({ code: 50020001, message: 'Training job not found' }, { status: 404 })
    const checkpoints = [
      { epoch: 1, step: 100, path: `/projects/${params.projectId}/training/${params.jobId}/checkpoint/epoch_1.pth`, is_best: false, metrics: { val_loss: 0.45 }, file_size: 45000000, created_at: job.created_at },
      { epoch: 5, step: 500, path: `/projects/${params.projectId}/training/${params.jobId}/checkpoint/epoch_5.pth`, is_best: true, metrics: { val_loss: 0.18 }, file_size: 45000000, created_at: job.updated_at },
    ]
    return HttpResponse.json({ code: 0, message: 'success', data: { checkpoints }, request_id: 'mock-training-checkpoints' })
  }),
]
