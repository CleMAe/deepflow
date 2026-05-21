import axios from 'axios'

export function formatApiError(err: unknown, fallback = '请求失败'): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as { message?: string; code?: number } | undefined
    if (data?.message) return data.message
    if (err.response?.status === 404) return '资源不存在，请先完成上一步操作'
  }
  if (err instanceof Error && err.message) return err.message
  return fallback
}
