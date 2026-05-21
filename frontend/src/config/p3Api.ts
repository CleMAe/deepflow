/**
 * P3 联调模式：为 false 时关闭 datasets / cleaning / EDA / augment 及 projects 的 MSW，
 * 请求走 Vite 代理 → 后端 (localhost:8000)。工作台须进入后端已 seed 的 Demo Project。
 */
export const p3UseMock = import.meta.env.VITE_P3_USE_MOCK !== 'false'
