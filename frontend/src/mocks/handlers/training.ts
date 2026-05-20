import { http, HttpResponse } from 'msw'
import type { components } from '@/api/types'

type TrainingStatus = components['schemas']['TrainingStatus']
type TrainingJob = components['schemas']['TrainingJob']

const mockJobs: TrainingJob[] = [
  {
    id: 'job-1',
    project_id: 'proj-1',
    name: 'ResNet-18 第一轮训练',
    model_id: 'model-1',
    dataset_id: 'ds-1',
    val_dataset_id: 'ds-1',
    hyperparams: { epochs: 10, batch_size: 32, learning_rate: 0.001, optimizer: 'adam', loss_function: 'cross_entropy', weight_decay: 0, lr_scheduler: 'none', grad_accum_steps: 1, mixed_precision: false, checkpoint_every_n_epochs: 1 },
    status: 'success',
    device: 'cuda',
    current_epoch: 10,
    total_epochs: 10,
    metrics: { train_loss: 0.12, val_loss: 0.18, accuracy: 0.92, best_val_loss: 0.15, best_accuracy: 0.93 },
    checkpoint: '/projects/proj-1/training/job-1/checkpoint/best.pth',
    started_at: '2026-05-19T08:00:00Z',
    finished_at: '2026-05-19T08:30:00Z',
    created_at: '2026-05-19T07:55:00Z',
    updated_at: '2026-05-19T08:30:00Z',
  },
  {
    id: 'job-2',
    project_id: 'proj-1',
    name: 'MLP 销售预测训练',
    model_id: 'model-2',
    dataset_id: 'ds-2',
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

const pollCounts = new Map<string, number>()

function nextStatus(status: TrainingStatus, action: 'start' | 'pause' | 'resume' | 'stop'): TrainingStatus {
  switch (action) {
    case 'start':
      return 'running'
    case 'pause':
      return 'paused'
    case 'resume':
      return 'running'
    case 'stop':
      return 'cancelled'
    default:
      return status
  }
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
    const body = (await request.json()) as { name: string; model_id: string; dataset_id: string; hyperparams?: Record<string, unknown>; device?: string; description?: string }
    const newJob: TrainingJob = {
      id: `job-${Math.random().toString(36).slice(2)}`,
      project_id: params.projectId as string,
      name: body.name,
      model_id: body.model_id,
      dataset_id: body.dataset_id,
      hyperparams: body.hyperparams ?? {},
      status: 'pending',
      device: body.device ?? 'auto',
      current_epoch: 0,
      total_epochs: (body.hyperparams as { epochs?: number })?.epochs ?? 10,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    mockJobs.push(newJob)
    pollCounts.set(newJob.id!, 0)
    return HttpResponse.json(
      { code: 0, message: 'success', data: newJob, request_id: 'mock-training-create' },
      { status: 201 }
    )
  }),

  http.get('/api/v1/projects/:projectId/training-jobs/:jobId', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) {
      return HttpResponse.json({ code: 40404, message: 'job not found' }, { status: 404 })
    }
    return HttpResponse.json({ code: 0, message: 'success', data: job, request_id: 'mock-training-get' })
  }),

  http.post('/api/v1/projects/:projectId/training-jobs/:jobId/start', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) return HttpResponse.json({ code: 40404, message: 'job not found' }, { status: 404 })
    job.status = nextStatus(job.status!, 'start')
    job.started_at = new Date().toISOString()
    job.updated_at = new Date().toISOString()
    return HttpResponse.json({ code: 0, message: 'success', data: job, request_id: 'mock-training-start' })
  }),

  http.post('/api/v1/projects/:projectId/training-jobs/:jobId/pause', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) return HttpResponse.json({ code: 40404, message: 'job not found' }, { status: 404 })
    job.status = nextStatus(job.status!, 'pause')
    job.updated_at = new Date().toISOString()
    return HttpResponse.json({ code: 0, message: 'success', data: job, request_id: 'mock-training-pause' })
  }),

  http.post('/api/v1/projects/:projectId/training-jobs/:jobId/resume', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) return HttpResponse.json({ code: 40404, message: 'job not found' }, { status: 404 })
    job.status = nextStatus(job.status!, 'resume')
    job.updated_at = new Date().toISOString()
    return HttpResponse.json({ code: 0, message: 'success', data: job, request_id: 'mock-training-resume' })
  }),

  http.post('/api/v1/projects/:projectId/training-jobs/:jobId/stop', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) return HttpResponse.json({ code: 40404, message: 'job not found' }, { status: 404 })
    job.status = nextStatus(job.status!, 'stop')
    job.finished_at = new Date().toISOString()
    job.updated_at = new Date().toISOString()
    return HttpResponse.json({ code: 0, message: 'success', data: job, request_id: 'mock-training-stop' })
  }),

  http.get('/api/v1/projects/:projectId/training-jobs/:jobId/logs', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) return HttpResponse.json({ code: 40404, message: 'job not found' }, { status: 404 })
    const logs = [
      { level: 'INFO', message: 'Training started', timestamp: job.started_at || job.created_at },
      { level: 'INFO', message: `Epoch ${job.current_epoch}/${job.total_epochs} - loss: ${job.metrics?.train_loss ?? 0.5}`, timestamp: job.updated_at },
    ]
    return HttpResponse.json({ code: 0, message: 'success', data: { logs }, request_id: 'mock-training-logs' })
  }),

  http.get('/api/v1/projects/:projectId/training-jobs/:jobId/checkpoints', ({ params }) => {
    const job = mockJobs.find((j) => j.id === params.jobId)
    if (!job) return HttpResponse.json({ code: 40404, message: 'job not found' }, { status: 404 })
    const checkpoints = [
      { epoch: 1, step: 100, path: `/projects/${params.projectId}/training/${params.jobId}/checkpoint/epoch_1.pth`, is_best: false, metrics: { val_loss: 0.45 }, file_size: 45000000, created_at: job.created_at },
      { epoch: 5, step: 500, path: `/projects/${params.projectId}/training/${params.jobId}/checkpoint/epoch_5.pth`, is_best: true, metrics: { val_loss: 0.18 }, file_size: 45000000, created_at: job.updated_at },
    ]
    return HttpResponse.json({ code: 0, message: 'success', data: { checkpoints }, request_id: 'mock-training-checkpoints' })
  }),
]
