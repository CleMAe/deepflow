# P4 Day3 开发日志：真实 API + WebSocket + 实验管理

> 日期：2026-05-20  
> 角色：P4 FE Dev（模型构建 + 训练监控）  
> 分支：`feat/P4-day3`

## 今日目标

Day3：训练/模型切真实 API（可选）、WebSocket 实时监控、实验管理 Tab；保留 MSW Mock 独立验收。

## 完成内容

1. **API 模式** — `lib/apiMode.ts` + `.env.development`（`VITE_USE_REAL_API`）
2. **MSW 条件启动** — `main.tsx`：真实模式不启动 MSW
3. **WebSocket** — `hooks/useTrainingWebSocket.ts`（metrics/progress/log/status_change）
4. **实验 API** — `api/experiments.ts`（list/get/update/compare）
5. **实验管理 UI** — `components/training/ExperimentsPanel.tsx`（第 4 Tab）
6. **训练监控页** — 合并 REST 日志 + WS/Mock 曲线；WS 失败回退 Mock
7. **Mock** — `experiments.ts` 补充 PUT handler

## 联调说明

```bash
# Mock（默认）
cd frontend && npm run dev

# 真实 API
# frontend/.env.development → VITE_USE_REAL_API=true
set PYTHONPATH=src && uvicorn app.main:app --reload --port 8000
```

Demo 项目：`11111111-1111-1111-1111-111111111111`

## 验证

```bash
cd frontend
npm run lint
npx tsc -b
npx -p node@20.19.0 node ./node_modules/vite/bin/vite.js build
```
