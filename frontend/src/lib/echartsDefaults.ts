import type { EChartsOption } from 'echarts'
import type { components } from '@/api/types'

type Visualization = components['schemas']['Visualization']

const BASE: EChartsOption = {
  tooltip: { trigger: 'axis' },
  grid: { left: 48, right: 24, top: 40, bottom: 40, containLabel: true },
}

export function mergeEChartsOption(viz: Visualization): EChartsOption | null {
  const raw = viz.config
  if (!raw || typeof raw !== 'object') return null
  const cfg = raw as EChartsOption
  const series = cfg.series
  const pie = Array.isArray(series) && series.some((s) => (s as { type?: string }).type === 'pie')
  return {
    ...BASE,
    ...cfg,
    tooltip: cfg.tooltip ?? (pie ? { trigger: 'item' } : BASE.tooltip),
  }
}
