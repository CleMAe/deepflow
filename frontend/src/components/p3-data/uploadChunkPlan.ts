import type { Dataset } from '@/api/datasets'

export type DatasetFileFormat = NonNullable<Dataset['format']>

export interface UploadChunkPlan {
  format: DatasetFileFormat
  chunkSize: number
  totalChunks: number
  chunks: Blob[]
  strategyLabel: string
}

const CHUNK_SIZE_BY_FORMAT: Record<DatasetFileFormat, number> = {
  csv: 512 * 1024,
  json: 1024 * 1024,
  image: 4 * 1024 * 1024,
  other: 2 * 1024 * 1024,
}

const STRATEGY_LABEL_BY_FORMAT: Record<DatasetFileFormat, string> = {
  csv: 'CSV · 512KB/片（适合表格文本）',
  json: 'JSON · 1MB/片（结构化数据）',
  image: '图像 · 4MB/片（大二进制块）',
  other: '其他 · 2MB/片（默认策略）',
}

export function detectDatasetFileFormat(file: File): DatasetFileFormat {
  const name = file.name.toLowerCase()
  const mime = file.type.toLowerCase()

  if (name.endsWith('.csv') || mime.includes('csv')) return 'csv'
  if (name.endsWith('.json') || name.endsWith('.jsonl') || mime.includes('json')) return 'json'
  if (mime.startsWith('image/') || /\.(png|jpe?g|gif|webp|bmp|tiff?)$/.test(name)) return 'image'
  return 'other'
}

export function getChunkSizeForFormat(format: DatasetFileFormat): number {
  return CHUNK_SIZE_BY_FORMAT[format]
}

export function formatChunkSizeLabel(bytes: number) {
  if (bytes >= 1024 * 1024) {
    const mb = bytes / (1024 * 1024)
    return Number.isInteger(mb) ? `${mb}MB` : `${mb.toFixed(1)}MB`
  }
  return `${Math.round(bytes / 1024)}KB`
}

export function resolveChunkSize(file: File, serverChunkSize?: number) {
  const format = detectDatasetFileFormat(file)
  const localSize = getChunkSizeForFormat(format)
  if (serverChunkSize && serverChunkSize > 0) {
    return serverChunkSize
  }
  return localSize
}

export function splitFileByChunkSize(file: File, chunkSize: number) {
  const chunks: Blob[] = []
  let offset = 0
  const safeChunkSize = Math.max(64 * 1024, chunkSize)

  while (offset < file.size) {
    chunks.push(file.slice(offset, offset + safeChunkSize))
    offset += safeChunkSize
  }

  return chunks.length > 0 ? chunks : [file]
}

export function buildUploadChunkPlan(file: File, serverChunkSize?: number): UploadChunkPlan {
  const format = detectDatasetFileFormat(file)
  const chunkSize = resolveChunkSize(file, serverChunkSize)
  const chunks = splitFileByChunkSize(file, chunkSize)

  return {
    format,
    chunkSize,
    totalChunks: chunks.length,
    chunks,
    strategyLabel: `${STRATEGY_LABEL_BY_FORMAT[format]}（${formatChunkSizeLabel(chunkSize)}/片，共 ${chunks.length} 片）`,
  }
}

export const UPLOAD_CHUNK_STRATEGY_HINT =
  '按文件类型自动分片：CSV 512KB · JSON 1MB · 图像 4MB · 其他 2MB；init 接口可返回推荐 chunk_size。'
