import { http, HttpResponse } from 'msw'
import type { components } from '@/api/types'

type CleaningResult = components['schemas']['CleaningResult']
type EDAReport = components['schemas']['EDAReport']
type AugmentResult = components['schemas']['AugmentResult']

const edaReports = new Map<string, EDAReport>()

function cleaningResult(datasetId: string, label: string): CleaningResult {
  return {
    dataset_id: datasetId,
    rows_before: 12000,
    rows_after: 11880,
    columns_affected: ['age', 'income'],
    changes_summary: { operation: label, mock: true },
  }
}

function buildMockEdaReport(datasetId: string): EDAReport {
  return {
    dataset_id: datasetId,
    created_at: new Date().toISOString(),
    summary: {
      num_rows: 12000,
      num_columns: 8,
      num_missing: 340,
      duplicate_rows: 12,
    },
    column_stats: [
      {
        name: 'sales',
        dtype: 'float64',
        missing_count: 0,
        missing_pct: 0,
        unique_count: 8900,
        mean: 1280.5,
        std: 420.2,
        min: 10,
        q25: 800,
        median: 1200,
        q75: 1600,
        max: 9000,
      },
      {
        name: 'region',
        dtype: 'object',
        missing_count: 12,
        missing_pct: 0.1,
        unique_count: 4,
        top_values: [
          { value: '华东', count: 4200 },
          { value: '华北', count: 3100 },
        ],
      },
    ],
    correlations: {
      sales: { sales: 1, visits: 0.62 },
      visits: { sales: 0.62, visits: 1 },
    },
    visualizations: [
      {
        type: 'histogram',
        title: '销售额分布（直方图）',
        config: {
          tooltip: { trigger: 'axis' },
          xAxis: { type: 'category', data: ['0-500', '500-1k', '1k-2k', '2k+'] },
          yAxis: { type: 'value' },
          series: [{ type: 'bar', data: [120, 240, 380, 90], name: '频数' }],
        },
      },
      {
        type: 'boxplot',
        title: '销售额箱线图',
        config: {
          tooltip: { trigger: 'item' },
          xAxis: { type: 'category', data: ['sales'] },
          yAxis: { type: 'value' },
          series: [
            {
              type: 'boxplot',
              data: [[10, 800, 1200, 1600, 9000]],
            },
          ],
        },
      },
      {
        type: 'heatmap',
        title: '数值列相关性热力图',
        config: {
          tooltip: { position: 'top' },
          grid: { height: '50%', top: '10%' },
          xAxis: { type: 'category', data: ['sales', 'visits'], splitArea: { show: true } },
          yAxis: { type: 'category', data: ['sales', 'visits'], splitArea: { show: true } },
          visualMap: { min: 0, max: 1, calculable: true, orient: 'horizontal', left: 'center', bottom: '5%' },
          series: [
            {
              type: 'heatmap',
              data: [
                [0, 0, 1],
                [0, 1, 0.62],
                [1, 0, 0.62],
                [1, 1, 1],
              ],
              label: { show: true },
            },
          ],
        },
      },
      {
        type: 'pie',
        title: '区域占比',
        config: {
          tooltip: { trigger: 'item' },
          series: [
            {
              type: 'pie',
              radius: '60%',
              data: [
                { value: 4200, name: '华东' },
                { value: 3100, name: '华北' },
                { value: 2800, name: '华南' },
                { value: 1900, name: '其他' },
              ],
            },
          ],
        },
      },
    ],
  }
}

export const p3CleaningHandlers = [
  http.post('/api/v1/projects/:projectId/datasets/:dsId/clean/missing', ({ params }) =>
    HttpResponse.json({
      code: 0,
      message: 'success',
      data: cleaningResult(params.dsId as string, 'missing'),
      request_id: 'mock-clean-missing',
    }),
  ),
  http.post('/api/v1/projects/:projectId/datasets/:dsId/clean/outlier', ({ params }) =>
    HttpResponse.json({
      code: 0,
      message: 'success',
      data: cleaningResult(params.dsId as string, 'outlier'),
      request_id: 'mock-clean-outlier',
    }),
  ),
  http.post('/api/v1/projects/:projectId/datasets/:dsId/clean/dedup', ({ params }) =>
    HttpResponse.json({
      code: 0,
      message: 'success',
      data: cleaningResult(params.dsId as string, 'dedup'),
      request_id: 'mock-clean-dedup',
    }),
  ),
  http.post('/api/v1/projects/:projectId/datasets/:dsId/clean/encode', ({ params }) =>
    HttpResponse.json({
      code: 0,
      message: 'success',
      data: cleaningResult(params.dsId as string, 'encode'),
      request_id: 'mock-clean-encode',
    }),
  ),
  http.post('/api/v1/projects/:projectId/datasets/:dsId/clean/type-convert', ({ params }) =>
    HttpResponse.json({
      code: 0,
      message: 'success',
      data: cleaningResult(params.dsId as string, 'type-convert'),
      request_id: 'mock-clean-type',
    }),
  ),
  http.post('/api/v1/projects/:projectId/datasets/:dsId/eda', ({ params }) => {
    const id = params.dsId as string
    const report = buildMockEdaReport(id)
    edaReports.set(`${params.projectId}:${id}`, report)
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: report,
      request_id: 'mock-eda-run',
    })
  }),
  http.get('/api/v1/projects/:projectId/datasets/:dsId/eda/report', ({ params }) => {
    const key = `${params.projectId}:${params.dsId as string}`
    const data = edaReports.get(key) ?? buildMockEdaReport(params.dsId as string)
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data,
      request_id: 'mock-eda-report',
    })
  }),
  http.post('/api/v1/projects/:projectId/datasets/:dsId/augment', async ({ request }) => {
    const body = (await request.json()) as { num_augmented?: number; output_dataset_name?: string }
    const result: AugmentResult = {
      original_count: 5000,
      augmented_count: 5000 * (body.num_augmented ?? 1),
      new_dataset_id: `ds-aug-${Date.now().toString(36)}`,
      output_dataset_name: body.output_dataset_name ?? 'augmented_set',
    }
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: result,
      request_id: 'mock-augment',
    })
  }),
]
