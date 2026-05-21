import type { Dataset } from '@/api/datasets'

export function isTabularDataset(d: Dataset | undefined): boolean {
  if (!d?.format) return false
  const f = d.format.toLowerCase()
  return f === 'csv' || f === 'json' || f === 'jsonl'
}

export function isImageDataset(d: Dataset | undefined): boolean {
  return d?.format?.toLowerCase() === 'image'
}

export function datasetOptionLabel(d: Dataset): string {
  return `${d.name ?? d.id} (${d.format ?? '?'})`
}
