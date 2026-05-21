/** When true, MSW is skipped and REST/WS go through Vite proxy to :8000. */
export function isRealApiMode() {
  return import.meta.env.VITE_USE_REAL_API === 'true'
}
