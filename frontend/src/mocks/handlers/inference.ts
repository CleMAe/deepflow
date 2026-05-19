import { http, HttpResponse } from 'msw'
import type { components } from '@/api/types'

type EvaluateRequest = components['schemas']['EvaluateRequest']
type OnlineInferenceRequest = components['schemas']['OnlineInferenceRequest']

export const inferenceHandlers = [
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
