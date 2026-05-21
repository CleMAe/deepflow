# DeepFlow 前端操作指南

> 日期：2026-05-21  
> 角色：P2 FE Lead  
> 适用范围：Day4 交付演示与前端本地联调

---

## 1. 启动前端

进入前端目录：

```bash
cd frontend
npm install
npm run dev
```

默认访问：

```text
http://localhost:5173
```

---

## 2. Mock 与真实 API 切换

前端环境变量在 `frontend/.env` 中配置，可从 `frontend/.env.example` 复制。

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

规则：

- P3/P4/P5 不需要删除各自的 MSW handler。
- 联调真实后端时只关闭 `VITE_ENABLE_MSW`。
- API 调用必须继续走 `frontend/src/lib/axios.ts`，不要在页面里直接使用原生 `fetch` 或新建 axios 实例。

---

## 3. 演示路径

推荐 Day4 演示按主流程走：

1. 登录或注册账号。
2. 进入工作台，选择 Demo Project。
3. 数据管理：上传或查看数据集。
4. 清洗 · EDA · 增强：执行清洗、生成 EDA、查看增强预览。
5. 模型构建：选择预置模型并保存项目模型。
6. 训练监控：创建训练任务，查看曲线、日志、Checkpoint 和实验对比。
7. 推理测试：执行在线测试、批量推理或模型评估。
8. Agent：创建 Agent，绑定模型工具，进入对话与 Prompt 管理。

---

## 4. Day4 前端体验约定

公共表格使用 `DataTable`：

- 默认空状态为“暂无数据”。
- `loading={true}` 默认显示“加载中”。
- 页面仍可通过 `locale.emptyText` 覆盖业务空态文案。

页面布局使用 `MainLayout`：

- 侧边栏在窄屏下自动收起。
- 主内容区域允许横向滚动，避免表格和图表挤压页面。
- 页面内业务错误提示由各模块继续使用 `Alert` / `message` 处理。

---

## 5. 验证命令

提交前至少执行：

```bash
cd frontend
npm run lint
npm test
npm run build
```

已知说明：

- `npm run build` 若出现 Vite chunk size warning，不属于阻塞错误。
- PowerShell 环境如遇 `npm.ps1` 执行策略问题，使用 `npm.cmd`。
