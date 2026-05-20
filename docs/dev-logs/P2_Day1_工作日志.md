# P2 Day1 工作日志：前端基础设施 Scaffold + Review 修复

> 日期：2026-05-19
> 角色：P2 FE Lead（前端负责人）
> 分支：`p2-frontend`（已删除）
> 主要提交：
> - `b93d863` feat: 完成p2核心功能
> - `d8be2b2` fix(frontend): P2 review fixes — antd v5, React 18, auth guard, lazy loading
> - `ada32f0` fix(frontend): tsconfig.app.json baseUrl 弃用修复 — TS 6 兼容
> PR：#2（scaffold 合并）、#3（review 修复合并）、#9（tsconfig 修复合并）

---

## 今日目标

完成 P2 Day1 范围：搭建完整的前端项目骨架，使 P3/P4/P5 能够基于统一基础设施并行开发页面。所有代码必须通过 lint、tsc 和 build。

---

## 完成内容

### 1. 前端脚手架搭建

- 初始化 Vite + React 18 + TypeScript 到 `frontend/` 目录
- 配置路径别名 `@/*` → `src/*`（Vite + TS 双配置）
- 配置 ESLint flat config（js, ts, react-hooks, react-refresh, prettier）
- 配置 Prettier（semi: false, singleQuote: true, tabWidth: 2, trailingComma: es5, printWidth: 100）

### 2. 核心依赖安装

```json
react ^18.2.0, react-dom ^18.2.0, antd ^5.22.0,
react-router-dom, zustand, axios, @tanstack/react-query,
msw, echarts-for-react
```

### 3. 目录结构与路由系统

- 建立 `src/pages/`, `src/components/`, `src/layouts/`, `src/stores/`, `src/lib/`, `src/mocks/`, `src/api/` 目录
- React Router v6 配置：
  - 公开路由：`/login`, `/register`
  - 受保护路由（RequireAuth）：`/dashboard`, `/projects/:projectId/*`
  - 项目子页面：data, cleaning, models, training, inference, agents
- 主布局 MainLayout：侧边栏导航 + Header + 可折叠 Sider

### 4. 状态管理与 HTTP 层

- **Zustand stores**：userStore（JWT + 登出）、projectStore、themeStore
- **Axios 实例**：baseURL `/api/v1`，请求拦截器自动注入 Bearer token，响应拦截器处理 401 refresh token 失败时跳转 `/login`
- **React Query**：queryClient 已配置，供服务端状态管理使用

### 5. Mock 服务（MSW）

- `src/mocks/browser.ts` 统一注册 handlers
- 已实现 handlers：
  - `auth.ts`：login, register, refresh, me
  - `projects.ts`：项目列表、创建、详情
  - `datasets.ts`：数据集列表、上传
- 响应格式严格遵循 `{code, message, data, request_id}`

### 6. 页面与组件骨架

- **页面**：LoginPage, RegisterPage, DashboardPage, ProjectDataPage, ProjectCleaningPage, ProjectModelsPage, ProjectTrainingPage, ProjectInferencePage, ProjectAgentsPage
- **通用组件**：
  - `FileUpload.tsx`：拖拽上传，Ant Design Upload 封装
  - `DataTable.tsx`：分页表格封装
  - `RequireAuth.tsx`：路由守卫（PR #3 新增）

### 7. 类型系统

- 使用 `openapi-typescript` 从 `docs/api/openapi.yaml` 生成 `src/api/types.ts`
- 全项目使用 `components['schemas']['xxx']` 作为类型源，确保前后端契约一致

### 8. 模块契约文档

- 编写 `src/README.md`，说明 HTTP 层、stores、components、routes、mock、types 的使用规范
- 目的：P3/P4/P5 无需反复询问即可上手开发

### 9. PR #2 合并与 Review 修复（PR #3）

P1 审查后，PR #3 修复了以下问题：

| # | 问题 | 修复 |
|---|---|---|
| 1 | antd v6 与契约规定 v5 不符 | `antd ^6.4.3` → `antd ^5.22.0` |
| 2 | React v19 与契约规定 v18 不符 | `react/react-dom ^19` → `^18.2.0` |
| 3 | FileUpload 进度条硬编码 50% | 改为从 `fileList[].percent` 读取真实进度 |
| 4 | 无路由守卫，未登录可访问所有页面 | 新增 `RequireAuth` 组件包裹受保护路由 |
| 5 | axios 拦截器已 unwrap data，页面多访问一层 | 修复 DashboardPage/ProjectDataPage/LoginPage 的双层 data 访问 |
| 6 | 主 bundle 1MB+ 无 code splitting | 项目页面改为 `React.lazy` 懒加载，主 bundle 1094KB → 757KB |

### 10. TypeScript 6 兼容修复（PR #9）

- 问题：`tsc -b` 报错 `TS5101: Option 'baseUrl' is deprecated`
- 根因修复：删除 `tsconfig.app.json` 中的 `"baseUrl": "."`，将 `"@/*": ["src/*"]` 改为 `"@/*": ["./src/*"]`
- 验证：`tsc -b`、`npm run build`、`npm run lint` 全部通过

---

## 验证结果

```bash
cd frontend
npm run lint         # ✅ 通过
./node_modules/.bin/tsc -b   # ✅ 通过
npm run build        # ✅ 通过，懒加载 chunk 正常生成
npm run dev          # ✅ localhost:5173 正常启动
```

本地页面验证：
- `/login` — 登录表单正常，Mock 登录后跳转 dashboard
- `/dashboard` — 页面渲染正常
- `/projects/:projectId/data` — 项目作用域路由正常
- 浏览器控制台显示 `[MSW] Mocking enabled`

---

## 遇到的问题

1. **openapi-typescript peer dependency 冲突**
   - 项目 TypeScript `~6.0.2`，openapi-typescript 要求 `^5.x`
   - 处理：通过 `npx openapi-typescript` 直接运行，不安装到项目依赖

2. **ESLint `no-explicit-any` 错误**
   - 初期部分页面使用 `any` 作为 API 响应类型
   - 处理：全部替换为 `components['schemas']` 生成类型或 `Record<string, unknown>`

3. **TypeScript 6 `baseUrl` 弃用**
   - P5 报告 `tsc -b` 失败，建议加 `ignoreDeprecations`
   - 处理：P2 评估后采用根因修复（删 baseUrl + 改 paths 为相对路径），而非 suppress

---

## 未完成内容

以下内容不属于 Day1 范围，留待 Day2/Day3：

- FileUpload 分片上传/断点续传（当前为单文件基础版）
- CodeEditor / JSON 配置编辑器组件（P4 需要）
- 各模块 MSW handler 细节补充（随 P3/P4/P5 页面开发跟进）
- ECharts 图表组件封装
- WebSocket 训练监控实时数据推送
- 单元测试覆盖（目前仅有 smoke test）

---

## Day2 建议

1. **FileUpload 分片上传**
   - 对接 P7 的分片上传 API（init → chunk → complete）
   - 添加进度条、断点续传、失败重试

2. **CodeEditor 组件**
   - 基于 Monaco Editor 或 CodeMirror 的轻量封装
   - 支持 JSON schema 校验（模型参数配置场景）

3. **MSW handlers 补全**
   - 随着 P3（数据清洗/EDA）、P4（模型/训练）、P5（推理/Agent）页面开发，及时补充 mock 数据

4. **P3/P4/P5 代码 Review**
   - 按规范审查 FE PR，确保符合已确立的组件/路由/store 约定

---

## 当前状态

P2 Day1 范围已完成，前端基础设施就绪，main 分支已对齐所有修复。P3/P4/P5 可基于当前 main 直接切 feature 分支并行开发。
