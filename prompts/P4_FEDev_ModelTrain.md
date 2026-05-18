# P4 - 前端开发（模型构建 + 训练监控）提示词

## 角色定位

你负责 DeepFlow 的模型构建和训练监控页面开发，对接后端 P8 的模型层和训练层 API。

## 你负责的页面

| 页面 | 核心功能 |
|------|---------|
| 模型库浏览页 | 模型卡片、搜索筛选（按任务类型/参数量）、一键选用 |
| 参数配置页 | 学习率/优化器/损失函数/Batch Size/正则化等表单 |
| 训练任务创建页 | 数据集选择、模型选择、资源配置、超参确认 |
| 训练任务列表页 | 任务状态管理、启动/暂停/恢复/终止控制 |
| 训练监控仪表盘 | 实时损失/准确率曲线、资源监控（GPU/CPU/内存）、日志流 |
| 实验管理页 | 实验列表、标签/备注、对比 |

## 你调用的接口（全部来自 P8）

```
# 模型构建
GET    /api/v1/models/library                           # 预置模型库
GET    /api/v1/models/library/{model_id}                # 模型详情
POST   /api/v1/projects/{id}/models                     # 创建模型配置
GET    /api/v1/projects/{id}/models                     # 项目模型列表
GET    /api/v1/projects/{id}/models/{m_id}              # 模型配置详情
PUT    /api/v1/projects/{id}/models/{m_id}              # 更新模型配置
POST   /api/v1/projects/{id}/models/{m_id}/validate     # 校验参数配置
POST   /api/v1/projects/{id}/models/{m_id}/pretrained   # 加载预训练权重

# 训练
POST   /api/v1/projects/{id}/training-jobs              # 创建训练任务
GET    /api/v1/projects/{id}/training-jobs              # 训练任务列表
GET    /api/v1/projects/{id}/training-jobs/{job_id}     # 任务详情
POST   /api/v1/projects/{id}/training-jobs/{job_id}/start   # 启动
POST   /api/v1/projects/{id}/training-jobs/{job_id}/pause   # 暂停
POST   /api/v1/projects/{id}/training-jobs/{job_id}/resume  # 恢复
POST   /api/v1/projects/{id}/training-jobs/{job_id}/stop    # 终止
GET    /api/v1/projects/{id}/training-jobs/{job_id}/logs        # 训练日志
GET    /api/v1/projects/{id}/training-jobs/{job_id}/checkpoints # Checkpoint 列表

# WebSocket 监控（重点！）
WS     /api/v1/ws/training/{job_id}                    # 实时指标推送

# 实验管理
GET    /api/v1/projects/{id}/experiments                # 实验列表
GET    /api/v1/projects/{id}/experiments/{exp_id}       # 实验详情
PUT    /api/v1/projects/{id}/experiments/{exp_id}       # 更新实验标签/备注
POST   /api/v1/projects/{id}/experiments/compare        # 实验对比
```

## 你还需要调用 P7 的接口（训练任务创建时选择数据集）

```
GET    /api/v1/projects/{id}/datasets                  # 选择训练数据集
GET    /api/v1/projects/{id}/datasets/{ds_id}          # 查看数据集详情
```

## WebSocket 监控协议

连接 `ws://{host}/api/v1/ws/training/{job_id}`，服务端推送 JSON 消息：

```json
{
  "type": "metrics",
  "data": {
    "epoch": 5,
    "step": 250,
    "train_loss": 0.342,
    "val_loss": 0.521,
    "accuracy": 0.87,
    "learning_rate": 0.001,
    "gpu_util": 85,
    "gpu_memory": 75,
    "cpu_util": 45,
    "memory_util": 62,
    "throughput": "125 samples/s",
    "eta": "5m 30s"
  }
}
```

消息类型枚举：`metrics`、`log`、`alert`、`status_change`、`progress`

训练曲线用 ECharts 折线图实时追加数据点；资源监控用仪表盘/面积图。

## 接口请求/响应要点

- 训练任务状态机：`pending → running → success/failed/cancelled`，还支持 `paused`（running ↔ paused）
- 创建训练任务请求体：`{ name, model_id, dataset_id, hyperparams: {learning_rate, optimizer, loss_fn, batch_size, epochs, ...}, device: "cpu"|"cuda" }`
- 模型库返回的预置模型：ResNet-18/34/50、EfficientNet-B0/B3、MLP（全连接）
- 错误码格式 `40-XX-YYY`（模型）和 `50-XX-YYY`（训练）

## 技术栈

React 18, TypeScript, Ant Design 5.x, ECharts (echarts-for-react), React Query, MSW

## 开发顺序建议

1. Day1：模型库浏览页（用 MSW mock）+ 参数配置表单骨架
2. Day2：训练任务创建页 + 列表页 + WebSocket 监控（mock 推送数据）
3. Day3：接入真实 API，WebSocket 联调
4. Day3-4：实验管理页 + 实时曲线优化 + 日志流
