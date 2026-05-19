import { http, HttpResponse } from 'msw'
import type { components } from '@/api/types'

type BatchInferenceRequest = components['schemas']['BatchInferenceRequest']
type EvaluateRequest = components['schemas']['EvaluateRequest']
type InferenceTask = components['schemas']['InferenceTask']
type OnlineInferenceRequest = components['schemas']['OnlineInferenceRequest']
type MockInferenceTask = InferenceTask & { polls: number; output_format: BatchInferenceRequest['output_format'] }

const mockModels = [
  {
    id: 'model-1',
    project_id: 'proj-1',
    name: 'ResNet-18 商品分类',
    arch_type: 'resnet18',
    params_cfg: {
      num_classes: 3,
      image_size: 224,
    },
    pretrained: true,
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
    params_cfg: {
      hidden_dims: [128, 64],
      output_dim: 1,
    },
    pretrained: false,
    model_path: '/projects/proj-1/models/model-2/checkpoint/latest.pth',
    description: '用于结构化业务数据回归预测',
    created_at: '2026-05-18T12:30:00Z',
    updated_at: '2026-05-18T12:30:00Z',
  },
]

const mockBatchTasks = new Map<string, MockInferenceTask>()

function toResponseTask(task: MockInferenceTask): InferenceTask {
  return {
    task_id: task.task_id,
    model_id: task.model_id,
    dataset_id: task.dataset_id,
    status: task.status,
    progress: task.progress,
    result_path: task.result_path,
    predictions: task.predictions,
    created_at: task.created_at,
    finished_at: task.finished_at,
  }
}

function buildMockPredictions(modelId?: string) {
  const imagePredictions = [
    { input: 'images/item_0001.jpg', prediction: '正常', confidence: 0.938 },
    { input: 'images/item_0002.jpg', prediction: '轻微异常', confidence: 0.874 },
    { input: 'images/item_0003.jpg', prediction: '正常', confidence: 0.911 },
    { input: 'images/item_0004.jpg', prediction: '严重异常', confidence: 0.816 },
  ]
  const tablePredictions = [
    { input: { row_id: 101, visits_30d: 18 }, prediction: 'high_value_customer', confidence: 0.921 },
    { input: { row_id: 102, visits_30d: 7 }, prediction: 'mid_value_customer', confidence: 0.783 },
    { input: { row_id: 103, visits_30d: 2 }, prediction: 'low_value_customer', confidence: 0.854 },
    { input: { row_id: 104, visits_30d: 13 }, prediction: 'high_value_customer', confidence: 0.889 },
  ]

  return modelId === 'model-1' ? imagePredictions : tablePredictions
}

export const inferenceHandlers = [
  http.get('/api/v1/projects/:projectId/models', ({ params }) => {
    const items = mockModels.filter((model) => model.project_id === params.projectId)

    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        page: 1,
        page_size: 20,
        total: items.length,
        items,
      },
      request_id: 'mock-p5-models',
    })
  }),

  http.post('/api/v1/projects/:projectId/inference/evaluate', async ({ request, params }) => {
    const payload = (await request.json()) as EvaluateRequest

    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        model_id: payload.model_id,
        dataset_id: payload.dataset_id,
        metrics: {
          accuracy: 0.914,
          precision: 0.902,
          recall: 0.887,
          f1: 0.894,
        },
        confusion_matrix: [
          [48, 3, 1],
          [4, 42, 5],
          [1, 2, 44],
        ],
        classification_report: {
          project_id: params.projectId,
          labels: ['正常', '轻微异常', '严重异常'],
        },
        num_samples: 150,
      },
      request_id: 'mock-p5-evaluate',
    })
  }),

  http.post('/api/v1/projects/:projectId/inference/batch', async ({ request, params }) => {
    const payload = (await request.json()) as BatchInferenceRequest
    const taskId = `task-${Date.now()}`
    const createdAt = new Date().toISOString()
    const task: MockInferenceTask = {
      task_id: taskId,
      model_id: payload.model_id,
      dataset_id: payload.dataset_id,
      status: 'running',
      progress: 36,
      result_path: `/projects/${params.projectId}/inference/${taskId}/predictions.${payload.output_format}`,
      predictions: [],
      created_at: createdAt,
      polls: 0,
      output_format: payload.output_format,
    }

    mockBatchTasks.set(taskId, task)

    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: toResponseTask(task),
      request_id: 'mock-p5-batch-start',
    })
  }),

  http.get('/api/v1/projects/:projectId/inference/:taskId', ({ params }) => {
    const taskId = String(params.taskId)
    const task = mockBatchTasks.get(taskId)

    if (!task) {
      return HttpResponse.json(
        {
          code: '60-04-001',
          message: 'inference task not found',
          data: null,
          request_id: 'mock-p5-batch-missing',
        },
        { status: 404 }
      )
    }

    const nextPolls = task.polls + 1
    const nextProgress = Math.min(100, (task.progress ?? 0) + 32)
    const nextTask: MockInferenceTask = {
      ...task,
      polls: nextPolls,
      progress: nextProgress,
      status: nextProgress >= 100 ? 'success' : 'running',
      predictions: nextProgress >= 100 ? buildMockPredictions(task.model_id) : task.predictions,
      finished_at: nextProgress >= 100 ? new Date().toISOString() : undefined,
    }

    mockBatchTasks.set(taskId, nextTask)

    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: toResponseTask(nextTask),
      request_id: 'mock-p5-batch-result',
    })
  }),

  http.post('/api/v1/projects/:projectId/inference/online', async ({ request }) => {
    const payload = (await request.json()) as OnlineInferenceRequest
    const isImageInput = typeof payload.input_data === 'string'

    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        prediction: isImageInput ? '轻微异常' : 'high_value_customer',
        confidence: isImageInput ? 0.873 : 0.921,
        probabilities: isImageInput
          ? {
              正常: 0.082,
              轻微异常: 0.873,
              严重异常: 0.045,
            }
          : {
              low_value_customer: 0.047,
              mid_value_customer: 0.032,
              high_value_customer: 0.921,
            },
        latency_ms: 37.6,
      },
      request_id: 'mock-p5-online',
    })
  }),
]
