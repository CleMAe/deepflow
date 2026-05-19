import { describe, expect, it } from 'vitest'
import {
  buildUploadChunkPlan,
  detectDatasetFileFormat,
  getChunkSizeForFormat,
} from '@/components/p3-data/uploadChunkPlan'

describe('uploadChunkPlan', () => {
  it('detects csv/json/image formats', () => {
    expect(detectDatasetFileFormat(new File(['a'], 'data.csv', { type: 'text/csv' }))).toBe('csv')
    expect(detectDatasetFileFormat(new File(['{}'], 'data.json', { type: 'application/json' }))).toBe(
      'json',
    )
    expect(detectDatasetFileFormat(new File([], 'pic.png', { type: 'image/png' }))).toBe('image')
  })

  it('uses different chunk sizes per format', () => {
    expect(getChunkSizeForFormat('csv')).toBe(512 * 1024)
    expect(getChunkSizeForFormat('json')).toBe(1024 * 1024)
    expect(getChunkSizeForFormat('image')).toBe(4 * 1024 * 1024)
  })

  it('splits a 2.5MB csv into multiple 512KB chunks', () => {
    const file = new File([new Uint8Array(2.5 * 1024 * 1024)], 'large.csv', { type: 'text/csv' })
    const plan = buildUploadChunkPlan(file)
    expect(plan.format).toBe('csv')
    expect(plan.totalChunks).toBeGreaterThan(4)
  })
})
