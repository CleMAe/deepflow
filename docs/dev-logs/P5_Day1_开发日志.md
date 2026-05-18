# P5 Day1 开发日志：推理评估 + 在线测试骨架

> 日期：2026-05-18  
> 角色：P5 FE Dev（推理 + Agent）  
> 分支：`feat/p5-inference-agent`  
> 提交：`b7a9838 feat(p5): add inference evaluation and online testing`  
> PR：<https://github.com/CleMAe/deepflow/pull/new/feat/p5-inference-agent>

## 今日目标

完成 P5 Day1 范围：基于 P2 前端骨架，实现推理模块的首版可运行页面骨架，优先覆盖“模型评估”和“在线测试”，使用 MSW Mock 数据完成前端独立验收。

## 完成内容

1. 合入 P2 前端骨架
   - 基于 `origin/feat/my-new-task` 合入 `frontend/` 工程。
   - 保持现有 React、Ant Design、React Query、Axios、MSW、ECharts 技术栈。

2. 实现推理测试页面
   - 替换 `frontend/src/pages/ProjectInferencePage.tsx` 占位内容。
   - 页面入口：`/projects/:projectId/inference`。
   - 使用 Tabs 拆分为“模型评估”和“在线测试”。

3. 模型评估功能
   - 支持选择模型、数据集和评估指标。
   - 调用 `POST /projects/{id}/inference/evaluate`。
   - 展示 accuracy、precision、recall、f1、样本数。
   - 使用 ECharts 渲染混淆矩阵热力图。

4. 在线测试功能
   - 支持选择模型并输入 JSON。
   - 请求体严格使用 OpenAPI 中的 `input_data` 字段。
   - 调用 `POST /projects/{id}/inference/online`。
   - 展示预测结果、置信度、延迟和类别概率。
   - 非法 JSON 会在前端拦截并提示，不发送请求。

5. API 与 Mock
   - 新增 `frontend/src/api/inference.ts`，封装 P5 推理 API。
   - 新增 `frontend/src/mocks/handlers/inference.ts`。
   - 注册以下 Mock 接口：
     - `GET /api/v1/projects/:projectId/models`
     - `POST /api/v1/projects/:projectId/inference/evaluate`
     - `POST /api/v1/projects/:projectId/inference/online`
   - 更新 `frontend/src/mocks/browser.ts` 注册 P5 handler。

## 验证结果

已通过：

```bash
npx tsc -b
npm run lint
npx -p node@20.19.0 node ./node_modules/vite/bin/vite.js build
```

本地页面验证：

```text
http://127.0.0.1:5173/projects/proj-1/inference
```

访问结果：HTTP 200，页面可打开。

## 遇到的问题

1. 本机 Node 版本偏低
   - 当前版本：`v20.15.0`
   - Vite 要求：`20.19+` 或 `22.12+`
   - 处理方式：临时使用 `npx -p node@20.19.0` 执行 Vite build。
   - 建议：团队统一升级到 Node `20.19.0+`。

2. ECharts 依赖缺失
   - `echarts-for-react` 构建时需要 `tslib`。
   - 已将 `tslib` 加入 `frontend/package.json` 依赖。

3. TypeScript 6 配置提示
   - `baseUrl` 在 TS 6 中有弃用提示。
   - 已在 `frontend/tsconfig.app.json` 增加 `ignoreDeprecations: "6.0"`，保证构建通过。

## 未完成内容

以下内容不属于 Day1 范围，暂未实现：

- 批量推理页面
- Agent 管理页面实装
- Agent 对话页
- SSE 流式响应
- Prompt 编辑器
- 对话日志页

## Day2 建议

1. 补齐批量推理
   - 实现数据集 + 模型选择。
   - 调用 `POST /inference/batch`。
   - 轮询 `GET /inference/{task_id}` 展示进度和结果。

2. 开始 Agent 管理骨架
   - Agent 列表。
   - 创建 Agent 表单。
   - 工具绑定入口。

3. 与 P1/P7/P8 对齐接口细节
   - 确认真实模型列表字段。
   - 确认评估返回的 `confusion_matrix` 类别标签来源。
   - 确认在线推理输入格式是否区分表格数据和图片 Base64。

## 当前状态

P5 Day1 范围已完成，可作为前端独立 Mock 验收版本继续推进。
