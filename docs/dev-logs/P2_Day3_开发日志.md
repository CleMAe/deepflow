# P2 Day3 工作日志：前端联调基础设施

> 日期：2026-05-21
> 角色：P2 FE Lead（前端负责人）
> 分支：`feat/p2-day3-fe-infra-integration`

---

## 今日目标

Day3 是集成日，团队需要从 Mock 开发切换到真实后端联调。P2 范围只覆盖前端公共基础设施，不接管 P3/P4/P5 的业务页面实现。

---

## 完成内容

### 1. MSW 启停开关

- 新增 `VITE_ENABLE_MSW`
- 默认开发环境继续启用 MSW
- 联调真实后端时设置 `VITE_ENABLE_MSW=false`
- 不删除任何模块 handler，避免影响 P3/P4/P5 并行开发

### 2. API Base URL 配置

- 新增 `VITE_API_BASE_URL`
- 未配置时默认 `/api/v1`
- 如需直连后端，可设置为 `http://localhost:8000/api/v1`

### 3. 前端环境示例

- 新增 `frontend/.env.example`
- 更新根目录 `.env.example`，补充前端联调变量说明

### 4. 前端契约文档更新

- 更新 `frontend/src/README.md`
- 增加 Day3 Mock / 真实 API 切换说明
- 修正 FileUpload 分片上传已完成的过期描述

---

## 给 P3/P4/P5 的接入说明

Mock 开发：

```bash
VITE_ENABLE_MSW=true
VITE_API_BASE_URL=/api/v1
```

真实后端联调：

```bash
VITE_ENABLE_MSW=false
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

各模块负责人继续维护自己的页面和 handler。若接口字段不匹配，优先在各模块 API wrapper 或后端契约处对齐，不要绕过 `src/lib/axios.ts`。

---

## 边界说明

- 未修改 P3 数据管理 / 清洗 EDA 页面业务逻辑
- 未修改 P4 模型 / 训练页面业务逻辑
- 未修改 P5 推理 / Agent 页面业务逻辑
- 未改动后端接口实现

