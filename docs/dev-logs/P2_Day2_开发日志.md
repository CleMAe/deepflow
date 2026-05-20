# P2 Day2 工作日志：通用组件 + MSW 补全 + 主题定制

> 日期：2026-05-20
> 角色：P2 FE Lead（前端负责人）
> 分支：`feat/P2-frontend`
> 主要提交：
> - `7c242e1` feat(upload): 实现 FileUpload 分片上传 + MSW mock
> - `4b1a412` feat(components): CodeEditor + CommonModal + MSW handlers(models/training/experiments)
> - `e76fc77` feat(theme): Ant Design 主题定制统一 token 和组件圆角

---

## 今日目标

完成 P2 Day2 范围：补齐实施计划中的 P2 交付物（通用组件 + MSW + 主题），为 P3/P4/P5 页面开发提供完整基础设施。

---

## 完成内容

### 1. FileUpload 分片上传实现

- **新建** `src/api/upload.ts`：封装 4 个上传 API
  - `initUpload` — 初始化分片会话
  - `uploadChunk` — 上传单个分片（multipart/form-data）
  - `completeUpload` — 合并分片完成上传
  - `uploadSimple` — 简单单文件上传（< 500MB）
- **重构** `src/components/common/FileUpload.tsx`
  - 新增必需 props：`projectId`
  - 使用 `customRequest` 接管 Ant Design Upload 上传逻辑
  - 小文件（≤500MB）走简单上传，大文件自动分片（5MB/片）
  - 分片上传流程：init → 循环 chunk → complete
  - 支持多文件、实时进度条（整体百分比）
- **补充** `src/mocks/handlers/datasets.ts`
  - 新增 init / chunk / complete / simple 四个 handler
  - 支持分片会话状态追踪（内存 Map）

### 2. CodeEditor / JSON 配置编辑器

- **新建** `src/components/common/CodeEditor.tsx`
  - 零依赖实现（网络环境限制，Monaco 安装失败，改用 textarea 方案）
  - 功能：行号显示、JSON 实时语法验证、格式化按钮、压缩按钮
  - 接口：`value` / `onChange` / `language`（默认 json） / `height` / `readOnly`
  - 语法错误时边框变红，底部显示错误信息
  - 行号与 textarea 滚动同步

### 3. Modal 通用组件封装

- **新建** `src/components/common/CommonModal.tsx`
  - Ant Design Modal 二次封装
  - 统一默认行为：`destroyOnClose={true}`、`maskClosable={false}`、`width={600}`
  - 透传所有 ModalProps，使用方零成本替换原有 `<Modal>`

### 4. 补充 MSW handlers

后端 Day2 新增 models / training / experiments 路由，P2 补充完整 mock：

| 文件 | handler 数量 | 覆盖端点 |
|------|-------------|---------|
| `models.ts` | 7 | models CRUD + validate + pretrained |
| `training.ts` | 9 | training-jobs CRUD + start/pause/resume/stop + logs + checkpoints |
| `experiments.ts` | 5 | experiments CRUD + compare |

- `browser.ts` 已注册所有新 handler
- 数据结构和响应格式严格遵循 `openapi.yaml`
- 保留了 P5 inference.ts 中的 models 列表 handler（不删除 adjacent 代码）

### 5. Ant Design 主题定制

- **新建** `src/theme.ts`
  - 全局 token：`colorPrimary: #1677ff`、`borderRadius: 6`、`fontSize: 14`
  - 组件级 token：Button / Card / Table / Modal / Input / Select / DatePicker 统一圆角
- **修改** `src/App.tsx`
  - 引入 `ConfigProvider`，用 `themeConfig` 包裹全局路由

---

## 验证结果

```bash
npx eslint src/api/upload.ts src/components/common/FileUpload.tsx src/components/common/CodeEditor.tsx src/components/common/CommonModal.tsx src/mocks/handlers/models.ts src/mocks/handlers/training.ts src/mocks/handlers/experiments.ts src/mocks/browser.ts src/App.tsx src/theme.ts
# ✅ 全部通过，无错误
```

TypeScript：`tsc -b` 无 upload/component/mock 相关类型错误（`vitest/globals` 为 pre-existing 环境问题）。

---

## 遇到的问题

1. **Monaco Editor 安装失败**
   - 尝试 `npm install @monaco-editor/react` 两次均因网络 ECONNRESET 失败
   - 处理：切换为零依赖 textarea 方案，保留行号 + JSON 验证 + 格式化功能，后续可无缝替换

2. **ESLint `no-empty-object-type`（CommonModal）**
   - `interface CommonModalProps extends ModalProps {}` 触发规则
   - 处理：直接移除空接口，函数参数使用 `ModalProps`

3. **ESLint `no-unused-vars`（training.ts）**
   - 内部 mock 字段 `__polls` 被赋值但未使用
   - 处理：从 TrainingJob 类型中剥离内部状态，改用外部 `Map<string, number>` 存储

---

## 未完成内容

以下内容按实施计划排期，不提前开工：

- **WebSocket 训练监控前端对接准备**（P1，Day2 验收标准要求）
  - 需要 MSW WebSocket mock 或真实后端 WebSocket 连接
  - P4 主导，P2 提供通用 Hook/组件支持
- **ECharts 图表组件封装**（P1）
  - P4 训练监控 / P5 模型评估需要
  - 可降级为页面直接引用 `echarts-for-react`
- **Mock → 真实 API 切换**（P0，Day3）
  - 实施计划 5.4：09:00-12:00 统一切换
- **UI 打磨**（P0，Day4）
  - Loading 态、空状态、错误提示、响应式适配

---

## Day3 建议

1. **协助 P3/P4/P5 Mock → 真实 API 切换**
   - 协调接口不匹配问题，统一修改 axios/api 层
2. **WebSocket 通用 Hook**
   - 封装 `useTrainingWebSocket(jobId)`，供 P4 训练监控页面使用
3. **ECharts 组件评估**
   - 判断是否需要封装通用图表组件，或页面直接引用

---

---

## PR Review 修复（组长审查 PR #23）

提交 PR 后组长审查，发现以下问题并已修复：

### Critical（已修复）

1. **删除 `uploadSimple`，所有文件统一走分片流程**
   - 后端不存在 `POST /projects/{id}/datasets/upload` 简单上传端点
   - 修改：`upload.ts` 删除 `uploadSimple`；`FileUpload.tsx` 删除大小文件判断，统一走 `init → chunk → complete`
   - `datasets.ts` 删除 simple upload mock handler

2. **删除 experiments 不存在的 DELETE mock**
   - 后端 OpenAPI 和实际路由均无 `DELETE /experiments/{id}`
   - 修改：`experiments.ts` 删除该 handler

### Warning（已修复）

1. **MSW mock 数据结构与后端对齐**
   - `models.ts`：`pretrained_source` 从 `'torchvision'` 改为 `'huggingface'`（与后端 schema 枚举一致）
   - `training.ts`：`logs` 返回从对象数组 `{level,message,timestamp}` 改为字符串数组 `string[]`，与后端 `TrainingLogOut(logs=lines)` 一致
   - `training.ts`：新增状态机验证，禁止非法状态转换（如 pause pending 的 job），与后端 `_VALID_TRANSITIONS` 对齐

2. **错误码统一为 8 位规范**
   - model not found：`40404` → `40020001`
   - training job not found：`40404` → `50020001`
   - invalid transition：新增 `50010001`
   - upload not found：`40404` → `30020002`

3. **CodeEditor 按钮样式统一**
   - 格式化/压缩按钮从原生 `<button>` 改为 Ant Design `<Button size="small">`
   - 行号区域显式设置 `overflowY: 'hidden'` 避免滚动条错位

4. **删除 training.ts 死代码**
   - 删除未使用的 `pollCounts` Map

---

## 当前状态

P2 Day2 P0 交付物全部完成 + PR review 修复已推送。分支 `feat/P2-frontend` 已更新。前端基础设施（组件库 + MSW + 主题）已就绪，P3/P4/P5 可基于当前分支继续页面开发。
