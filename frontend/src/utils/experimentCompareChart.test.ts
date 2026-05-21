import { describe, expect, it } from 'vitest'

import { buildExperimentCompareChartOption } from './experimentCompareChart'

describe('buildExperimentCompareChartOption', () => {
  it('binds metric values to compareResult.experiments order, not UI selection order', () => {
    const option = buildExperimentCompareChartOption({
      experiments: [
        { id: 'exp-b', name: '实验 B' },
        { id: 'exp-a', name: '实验 A' },
      ],
      metric_comparison: {
        accuracy: [0.82, 0.91],
        f1: [0.8, 0.9],
      },
    })

    expect(option?.legend.data).toEqual(['实验 B', '实验 A'])
    expect(option?.series[0].name).toBe('实验 B')
    expect(option?.series[0].data).toEqual([0.82, 0.8])
    expect(option?.series[1].name).toBe('实验 A')
    expect(option?.series[1].data).toEqual([0.91, 0.9])
  })

  it('returns null when comparison payload is empty', () => {
    expect(buildExperimentCompareChartOption({ experiments: [], metric_comparison: {} })).toBeNull()
    expect(buildExperimentCompareChartOption(null)).toBeNull()
  })
})
