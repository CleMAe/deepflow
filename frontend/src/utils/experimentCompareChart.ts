import type { components } from '@/api/types'

export type ExperimentComparison = components['schemas']['ExperimentComparison']

export type ExperimentCompareChartOption = {
  tooltip: { trigger: 'axis' }
  legend: { data: string[] }
  xAxis: { type: 'category'; data: string[] }
  series: Array<{
    name: string
    type: 'bar'
    data: number[]
  }>
}

/** Chart series order follows {@link ExperimentComparison.experiments}, aligned with metric_comparison indices. */
export function buildExperimentCompareChartOption(
  compareResult: ExperimentComparison | null | undefined,
): ExperimentCompareChartOption | null {
  const experiments = compareResult?.experiments ?? []
  const mc = compareResult?.metric_comparison ?? {}
  const keys = Object.keys(mc)
  if (!keys.length || !experiments.length) return null

  const seriesNames = experiments.map(
    (exp, index) => exp.name ?? exp.id ?? `实验 ${index + 1}`,
  )

  return {
    tooltip: { trigger: 'axis' },
    legend: { data: seriesNames },
    xAxis: { type: 'category', data: keys },
    series: experiments.map((exp, index) => ({
      name: exp.name ?? exp.id ?? `实验 ${index + 1}`,
      type: 'bar',
      data: keys.map((k) => {
        const v = mc[k]?.[index]
        return typeof v === 'number' ? v : 0
      }),
    })),
  }
}
