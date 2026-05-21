import type { CSSProperties } from 'react'
import type { AugmentTransform } from '@/api/cleaningEda'

/** 前端预览：用 CSS 近似展示增强效果（提交后仍以服务端 Pillow 为准） */
export function buildAugmentPreviewStyle(
  transforms: AugmentTransform[],
  intensity: number,
): CSSProperties {
  const t = intensity
  let transform = ''
  const filter: string[] = []

  for (const tr of transforms) {
    switch (tr.type) {
      case 'rotate':
        transform += ` rotate(${Math.round(5 + t * 25)}deg)`
        break
      case 'flip_horizontal':
        transform += ' scaleX(-1)'
        break
      case 'flip_vertical':
        transform += ' scaleY(-1)'
        break
      case 'color_jitter':
        filter.push(`brightness(${1 + t * 0.2})`, `contrast(${1 + t * 0.15})`, `saturate(${1 + t * 0.25})`)
        break
      case 'gaussian_blur':
        filter.push(`blur(${0.5 + t * 2}px)`)
        break
      case 'random_crop':
        transform += ' scale(1.08)'
        break
      default:
        break
    }
  }

  return {
    transform: transform.trim() || undefined,
    filter: filter.length ? filter.join(' ') : undefined,
    transition: 'all 0.2s ease',
  }
}
