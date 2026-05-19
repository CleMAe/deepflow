import type { Dataset } from '@/api/datasets'

export const DATASET_FORMAT_OPTIONS: { label: string; value: Dataset['format'] }[] = [
  { label: 'CSV', value: 'csv' },
  { label: 'JSON', value: 'json' },
  { label: '图像', value: 'image' },
  { label: '其他', value: 'other' },
]

export const DATASET_STATUS_OPTIONS: { label: string; value: Dataset['status'] }[] = [
  { label: '上传中', value: 'uploading' },
  { label: '就绪', value: 'ready' },
  { label: '清洗中', value: 'cleaning' },
  { label: '已清洗', value: 'cleaned' },
  { label: '异常', value: 'error' },
]

export function formatDatasetStatus(status?: Dataset['status']) {
  return DATASET_STATUS_OPTIONS.find((item) => item.value === status)?.label ?? status ?? '-'
}

export function formatDatasetFormat(format?: Dataset['format']) {
  return DATASET_FORMAT_OPTIONS.find((item) => item.value === format)?.label ?? format ?? '-'
}
