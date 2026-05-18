# P8 - 后端开发（模型层 API + 训练引擎）提示词

## 角色定位

你负责 DeepFlow 的模型库 API、训练引擎核心、WebSocket 监控和实验管理，对接前端 P4 的页面。

## 你负责的 API 端点

```
# ============ 模型构建 ============
GET    /api/v1/models/library                           # 预置模型库
GET    /api/v1/models/library/{model_id}                # 模型详情
POST   /api/v1/projects/{id}/models                     # 创建模型配置
GET    /api/v1/projects/{id}/models                     # 项目模型列表
GET    /api/v1/projects/{id}/models/{m_id}              # 模型配置详情
PUT    /api/v1/projects/{id}/models/{m_id}              # 更新模型配置
POST   /api/v1/projects/{id}/models/{m_id}/validate     # 校验参数配置
POST   /api/v1/projects/{id}/models/{m_id}/pretrained   # 加载预训练权重

# ============ 训练 ============
POST   /api/v1/projects/{id}/training-jobs              # 创建训练任务
GET    /api/v1/projects/{id}/training-jobs              # 训练任务列表
GET    /api/v1/projects/{id}/training-jobs/{job_id}     # 任务详情
POST   /api/v1/projects/{id}/training-jobs/{job_id}/start   # 启动
POST   /api/v1/projects/{id}/training-jobs/{job_id}/pause   # 暂停
POST   /api/v1/projects/{id}/training-jobs/{job_id}/resume  # 恢复
POST   /api/v1/projects/{id}/training-jobs/{job_id}/stop    # 终止
GET    /api/v1/projects/{id}/training-jobs/{job_id}/logs        # 训练日志
GET    /api/v1/projects/{id}/training-jobs/{job_id}/checkpoints # Checkpoint 列表

# ============ WebSocket 监控 ============
WS     /api/v1/ws/training/{job_id}                    # 实时指标推送

# ============ 实验管理 ============
GET    /api/v1/projects/{id}/experiments                # 实验列表
GET    /api/v1/projects/{id}/experiments/{exp_id}       # 实验详情
PUT    /api/v1/projects/{id}/experiments/{exp_id}       # 更新实验标签/备注
POST   /api/v1/projects/{id}/experiments/compare        # 实验对比
```

## 你依赖的接口（其他模块）

| 来源 | 接口 | 用途 |
|------|------|------|
| P6 | JWT 认证中间件 | 所有 API 鉴权 |
| P6 | 数据库 Session | 操作 models / training_jobs / experiments 表 |
| P6 | 文件存储服务 | 模型文件存储到 `models/{model_uuid}/checkpoint/` 和 `exported/` |
| P7 | `GET /projects/{id}/datasets/{ds_id}` | 训练任务获取数据集信息和文件路径 |
| P7 | 数据集文件路径 | 训练引擎读取 `datasets/{ds_id}/raw/` 或 `cleaned/` 中的数据 |

## 数据模型

```
models:  id(UUID), project_id(FK), name, arch_type, params_cfg(JSONB), pretrained(bool), model_path, created_at
training_jobs: id(UUID), project_id(FK), name, model_id(FK→models), dataset_id(FK→datasets),
               hyperparams(JSONB), status(Enum), device, metrics(JSONB),
               checkpoint, started_at, finished_at
experiments: id(UUID), project_id(FK), job_id(FK→training_jobs), metrics(JSONB),
             params_snap(JSONB), tags(JSONB), notes, created_at
```

训练任务状态机：`pending → running → success / failed / cancelled`，还支持 `running ↔ paused`

## 关键业务逻辑

### 训练引擎核心
- **训练循环**作为独立子进程运行（`subprocess`），与 API 服务进程隔离
- API 进程通过文件系统（checkpoint 路径）+ 数据库（状态/指标）+ WebSocket 与训练子进程交互
- 支持混合精度训练（FP16/BF16）
- 支持梯度累积
- Checkpoint 自动保存 + 指定加载恢复训练
- 早停机制：验证损失连续 N 轮不下降则自动停止

### 预置模型库
| 任务类型 | 模型 |
|---------|------|
| 图像分类 | ResNet-18/34/50, EfficientNet-B0/B3 |
| 回归预测 | MLP（全连接网络） |

### WebSocket 推送协议

```json
{
  "type": "metrics",
  "data": {
    "epoch": 5, "step": 250,
    "train_loss": 0.342, "val_loss": 0.521, "accuracy": 0.87,
    "learning_rate": 0.001,
    "gpu_util": 85, "gpu_memory": 75, "cpu_util": 45, "memory_util": 62,
    "throughput": "125 samples/s", "eta": "5m 30s"
  }
}
```

消息类型：`metrics`、`log`、`alert`、`status_change`、`progress`

### 创建训练任务请求体
```json
{
  "name": "resnet50-cifar10-v1",
  "model_id": "uuid",
  "dataset_id": "uuid",
  "hyperparams": {
    "learning_rate": 0.001,
    "optimizer": "adam",
    "loss_fn": "cross_entropy",
    "batch_size": 32,
    "epochs": 50,
    "weight_decay": 0.0001,
    "lr_scheduler": "cosine"
  },
  "device": "cuda"
}
```

## 你提供给 P1（Agent 引擎）的依赖

P1 的 Agent 绑定模型工具时需要调用：
- `GET /projects/{id}/models/{m_id}` — 获取模型信息
- `POST /projects/{id}/inference/online` — Agent 通过推理接口调用模型

## 接口规范

- 统一响应：`{ code: 0, message: "success", data: {...}, request_id: "uuid" }`
- 分页：`{ page, page_size, total, items[] }`
- 错误码：`40-XX-YYY`（模型）、`50-XX-YYY`（训练）

## 技术栈

Python 3.10, FastAPI, SQLAlchemy 2.0, PyTorch 2.x, torchvision, ONNX Runtime 1.18+, WebSocket

## 开发顺序建议

1. Day1 上午：Router 骨架 + Mock handler + 模型库静态 JSON
2. Day1 晚：训练引擎核心（合成数据 + 最小训练循环验证 PyTorch 通路）
3. Day2 上午：训练循环完整实现（混合精度 + 梯度累积 + Checkpoint + 早停）
4. Day2 下午：WebSocket 监控推送 + 状态机（启动/暂停/恢复/终止）
5. Day3：实验管理 + 预训练权重加载 + 联调
