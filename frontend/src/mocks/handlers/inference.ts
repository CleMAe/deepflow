import { http, HttpResponse } from 'msw'
import type { components } from '@/api/types'

type EvaluateRequest = components['schemas']['EvaluateRequest']
type OnlineInferenceRequest = components['schemas']['OnlineInferenceRequest']

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
