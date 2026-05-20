# P4 Day2 开发日志：训练任务 + Mock 实时监控

> 日期：2026-05-19  
> 角色：P4 FE Dev（模型构建 + 训练监控）  
> 分支：`feat/P4-day2`

## 今日目标

完成 P4 Day2：训练任务创建页、任务列表（启停控制）、WebSocket 监控 Mock + ECharts 实时曲线。

## 完成内容

1. **API 封装** — `frontend/src/api/training.ts`
2. **Mock WS 推送** — `frontend/src/hooks/useTrainingMetricsMock.ts`
3. **训练监控页** — 重写 `ProjectTrainingPage.tsx`（任务列表 / 创建 / 监控三 Tab）
4. **Mock 小改** — `training.ts` 支持 `val_dataset_id`；`datasets.ts` 按项目过滤
5. **Vite** — `host: true`、`proxy.ws: true`（为 Day3 联调预埋）

## 验证

```bash
cd frontend
npm run lint
npx tsc -b
npx -p node@20.19.0 node ./node_modules/vite/bin/vite.js build
```

页面：`/projects/proj-1/training`

## Day3 计划

接入 P8 真实 API + 真实 WebSocket；实验管理页。
