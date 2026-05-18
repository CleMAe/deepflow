# P7 - 后端开发（数据层 API + 清洗引擎）提示词

## 角色定位

你负责 DeepFlow 的数据管理 API、数据清洗引擎、EDA 服务和数据增强服务，对接前端 P3 的页面。

## 你负责的 API 端点

```
# ============ 数据管理 ============
POST   /api/v1/projects/{id}/datasets/upload/init              # 初始化上传，返回 upload_id
POST   /api/v1/projects/{id}/datasets/upload/{uid}/chunk       # 上传分片（Content-Range header）
POST   /api/v1/projects/{id}/datasets/upload/{uid}/complete    # 合并分片，生成数据集
GET    /api/v1/projects/{id}/datasets                          # 数据集列表（分页）
POST   /api/v1/projects/{id}/datasets                          # 创建数据集（元数据注册）
GET    /api/v1/projects/{id}/datasets/{ds_id}                  # 数据集详情
GET    /api/v1/projects/{id}/datasets/{ds_id}/preview          # 数据预览（前100行）
GET    /api/v1/projects/{id}/datasets/{ds_id}/images           # 图片画廊（缩略图+标签）
PUT    /api/v1/projects/{id}/datasets/{ds_id}/labels           # 批量更新图片标签
PUT    /api/v1/projects/{id}/datasets/{ds_id}                  # 更新数据集
DELETE /api/v1/projects/{id}/datasets/{ds_id}                  # 删除数据集

# ============ 数据清洗 ============
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/missing    # 缺失值处理
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/outlier    # 异常值检测
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/dedup      # 去重
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/encode     # 编码转换
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/type-convert  # 类型转换

# ============ EDA ============
POST   /api/v1/projects/{id}/datasets/{ds_id}/eda              # 触发一键 EDA
GET    /api/v1/projects/{id}/datasets/{ds_id}/eda/report       # 获取 EDA 报告

# ============ 数据增强 & 划分 ============
POST   /api/v1/projects/{id}/datasets/{ds_id}/augment          # CV 数据增强
POST   /api/v1/projects/{id}/datasets/{ds_id}/split            # 数据集划分
```

## 你还需要实现的推理相关端点（与 P8 协作）

```
POST   /api/v1/projects/{id}/inference/evaluate    # 模型评估
POST   /api/v1/projects/{id}/inference/batch       # 批量推理
GET    /api/v1/projects/{id}/inference/{task_id}   # 推理结果查询
POST   /api/v1/projects/{id}/inference/online      # 在线测试（单条）
POST   /api/v1/projects/{id}/inference/export-onnx # 导出 ONNX
```

> 推理端点的模型加载和推理核心逻辑由 P8 提供，你负责 API 路由和请求编排。与 P1 协商分工。

## 你依赖的接口（P6 提供）

| 接口 | 用途 |
|------|------|
| JWT 认证中间件 | 所有 API 需鉴权 |
| RBAC 权限装饰器 | 检查用户对项目的操作权限 |
| 文件存储服务 | 上传文件存储到 `{STORAGE_ROOT}/projects/{id}/datasets/` |
| 数据库 Session | 操作 datasets 表 |

## 数据模型

`datasets` 表字段：`id(UUID), name, project_id(FK), format, file_path, num_samples, columns_meta(JSONB), tags(JSONB), status, created_at`

## 关键业务逻辑

### 分片上传流程
1. `upload/init` → 生成 `upload_id`，在 `{STORAGE_ROOT}/uploads/{upload_id}/` 创建临时目录
2. `upload/{uid}/chunk` → 按 `Content-Range` 写入分片到临时目录
3. `upload/{uid}/complete` → 合并分片 → 解析文件格式 → 提取元数据（样本数、列信息）→ 移动到 `datasets/{ds_id}/raw/` → 创建数据集记录

### 数据清洗
- 每个清洗操作生成新的 `cleaned/` 版本，不覆盖原始数据
- 支持格式：CSV、JSON、Parquet、Excel、图像
- 编码方式：One-Hot、Label、Target、Ordinal
- 缺失值策略：删除、填充（均值/中位数/众数/自定义值）、插值
- 异常值检测：Z-Score、IQR、自定义规则

### EDA 报告内容
- 统计概览：样本数、特征数、缺失率、数据类型分布、基本统计量
- 分布数据：直方图、箱线图、相关性热力图、类别分布（供前端 ECharts 渲染）
- 数据集划分：按比例划分训练/验证/测试集，支持分层抽样

### CV 数据增强
- 旋转、翻转、裁剪、色彩变换、MixUp、CutMix
- 用户选择增强强度（轻度/标准/强），自动应用预设参数组合
- 增强结果存入新数据集

## 接口规范

- 统一响应格式：`{ code: 0, message: "success", data: {...}, request_id: "uuid" }`
- 分页：`{ page, page_size, total, items[] }`
- 错误码：`30-XX-YYY`（数据集模块）
- 文件上传：`multipart/form-data`，分片用 `Content-Range` header

## 技术栈

Python 3.10, FastAPI, SQLAlchemy 2.0, pandas, Pillow, torchvision（数据增强）

## 开发顺序建议

1. Day1 上午：FastAPI Router 骨架 + 第一版 Mock handler
2. Day1 下午：数据上传 API（分片上传完整流程）
3. Day2 上午：数据清洗引擎（缺失值/异常值/去重）
4. Day2 下午：EDA 服务 + 数据增强服务
5. Day3：数据集划分 + 推理端点 + 联调
