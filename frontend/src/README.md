# DeepFlow 前端模块契约（P2 基础设施）

> 本文档描述 P2 提供的基础设施接口，供 P3/P4/P5 开发页面时参考。
> 所有类型均从 `openapi.yaml` 自动生成，见 `src/api/types.ts`。

---

## 1. HTTP 层 — `src/lib/axios.ts`

Axios 实例已封装好 baseURL、JWT 注入、token 刷新。

```tsx
import api from '@/lib/axios'
import type { components } from '@/api/types'

// GET 示例
const res = await api.get('/projects') as { data: components['schemas']['PaginatedProjects'] }

// POST 示例
const res = await api.post('/auth/login', { username, password }) as { data: components['schemas']['TokenPair'] }
```

**注意**：Axios interceptor 已把 `response.data` 直接返回，所以返回值就是 `ApiResponse.data` 部分。

---

## 2. 全局状态 — `src/stores/`

### `useUserStore`

| 字段/方法 | 类型 | 说明 |
|-----------|------|------|
| `user` | `User \| null` | 当前登录用户 |
| `token` | `string \| null` | access_token（自动读写 localStorage） |
| `setUser` | `(user) => void` | 设置用户信息 |
| `setToken` | `(token) => void` | 设置 token（自动持久化） |
| `logout` | `() => void` | 清除登录态并跳转（store 内部已处理） |

```tsx
import { useUserStore } from '@/stores/userStore'

const user = useUserStore((s) => s.user)
const logout = useUserStore((s) => s.logout)
```

### `useProjectStore`

| 字段/方法 | 类型 | 说明 |
|-----------|------|------|
| `currentProject` | `Project \| null` | 当前选中的项目 |
| `projects` | `Project[]` | 项目列表（Dashboard 已预加载） |
| `setCurrentProject` | `(project) => void` | 切换当前项目 |
| `setProjects` | `(projects) => void` | 批量设置项目列表 |

```tsx
import { useProjectStore } from '@/stores/projectStore'

const project = useProjectStore((s) => s.currentProject)
```

### `useThemeStore`

| 字段/方法 | 类型 | 说明 |
|-----------|------|------|
| `isDark` | `boolean` | 当前是否为暗色主题 |
| `toggleTheme` | `() => void` | 切换主题 |

---

## 3. 通用组件 — `src/components/common/`

### `<FileUpload>`

基础拖拽上传组件，内部使用 Ant Design Upload.Dragger。

```tsx
import FileUpload from '@/components/common/FileUpload'

<FileUpload
  action="/api/v1/projects/{projectId}/datasets/upload"
  multiple
  accept=".csv,.json,image/*"
  onSuccess={(files) => console.log(files)}
/>
```

| Props | 类型 | 必填 | 说明 |
|-------|------|------|------|
| `action` | `string` | ✅ | 上传接口地址 |
| `multiple` | `boolean` | ❌ | 是否多选 |
| `accept` | `string` | ❌ | 接受的文件类型 |
| `onSuccess` | `(files) => void` | ❌ | 上传成功回调 |

**注意**：分片上传（`upload/init → chunk → complete`）尚未实现，Day 2 补齐。

### `<DataTable>`

基于 Ant Design Table 的封装，自带分页。

```tsx
import DataTable from '@/components/common/DataTable'
import type { components } from '@/api/types'

type Dataset = components['schemas']['Dataset']

<DataTable<Dataset>
  columns={[{ title: '名称', dataIndex: 'name' }]}
  dataSource={datasets}
  loading={isLoading}
/>
```

| Props | 类型 | 说明 |
|-------|------|------|
| `columns` | `ColumnsType<T>` | 同 antd Table |
| `dataSource` | `T[]` | 数据源 |
| `loading` | `boolean` | 加载态 |

---

## 4. 路由约定

| 路由 | 页面 | 负责 |
|------|------|------|
| `/login` | LoginPage | P2 |
| `/register` | RegisterPage | P2 |
| `/dashboard` | DashboardPage | P2 |
| `/projects/:projectId/data` | ProjectDataPage | P3 |
| `/projects/:projectId/cleaning` | ProjectCleaningPage | P3 |
| `/projects/:projectId/models` | ProjectModelsPage | P4 |
| `/projects/:projectId/training` | ProjectTrainingPage | P4 |
| `/projects/:projectId/inference` | ProjectInferencePage | P5 |
| `/projects/:projectId/agents` | ProjectAgentsPage | P5 |

所有项目子页面共用 `MainLayout`（侧边栏 + Header），侧边栏会根据 `:projectId` 动态展开对应模块菜单。

---

## 5. Mock 服务 — `src/mocks/`

MSW 在开发环境自动启动，拦截以下接口：

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `GET /api/v1/projects`
- `GET /api/v1/projects/:id`
- `POST /api/v1/projects`
- `GET /api/v1/projects/:projectId/datasets`
- `GET /api/v1/projects/:projectId/datasets/:dsId`

**各模块自行补充 handler**：在 `src/mocks/handlers/` 下新建文件，然后在 `browser.ts` 中注册。

---

## 6. 关键类型速查

从 `src/api/types.ts` 提取的常用类型：

```ts
import type { components } from '@/api/types'

type User = components['schemas']['User']
type Project = components['schemas']['Project']
type Dataset = components['schemas']['Dataset']
type PaginatedProjects = components['schemas']['PaginatedProjects']
type PaginatedDatasets = components['schemas']['PaginatedDatasets']
type TokenPair = components['schemas']['TokenPair']
type EDAReport = components['schemas']['EDAReport']
type CleaningResult = components['schemas']['CleaningResult']
type Model = components['schemas']['Model']
```

---

## 7. 开发规范

- 所有 API 请求走 `api` 实例，**不要**直接调用 `axios.get`
- 状态管理优先用 Zustand，局部状态用 `useState`
- 列表数据请求用 React Query（`useQuery`），不要手写 `useEffect + fetch`
- Mock handler 按模块分文件放在 `src/mocks/handlers/`
- 组件 props 优先用具体类型，避免 `any`
