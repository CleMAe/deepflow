# P3 - 前端开发（数据管理 + 清洗/EDA）提示词

## 角色定位

你负责 DeepFlow 的数据管理和数据清洗/EDA 页面开发，对接后端 P7 的数据层 API。

## 你负责的页面

| 页面 | 核心功能 |
|------|---------|
| 数据上传页 | 拖拽上传、进度条、断点续传、格式自动识别 |
| 数据集列表页 | CRUD、搜索、标签筛选、分页 |
| 图片画廊页 | 缩略图列表、标签绑定、图片预览 |
| 数据清洗操作页 | 缺失值/异常值/去重/编码转换/类型转换 UI |
| EDA 报告页 | 统计概览、分布直方图、箱线图、热力图、饼图 |
| 数据增强配置页 | CV 增强参数（旋转/翻转/色彩/MixUp/CutMix）、强度选择、预览对比 |

## 你调用的接口（全部来自 P7）

```
# 数据管理
POST   /api/v1/projects/{id}/datasets/upload/init              # 初始化上传，获取 upload_id
POST   /api/v1/projects/{id}/datasets/upload/{uid}/chunk       # 上传分片
POST   /api/v1/projects/{id}/datasets/upload/{uid}/complete    # 合并分片
GET    /api/v1/projects/{id}/datasets                          # 数据集列表
POST   /api/v1/projects/{id}/datasets                          # 创建数据集（元数据注册）
GET    /api/v1/projects/{id}/datasets/{ds_id}                  # 数据集详情
GET    /api/v1/projects/{id}/datasets/{ds_id}/preview          # 数据预览（前100行）
GET    /api/v1/projects/{id}/datasets/{ds_id}/images           # 图片画廊（缩略图+标签）
PUT    /api/v1/projects/{id}/datasets/{ds_id}/labels           # 批量更新图片标签
PUT    /api/v1/projects/{id}/datasets/{ds_id}                  # 更新数据集
DELETE /api/v1/projects/{id}/datasets/{ds_id}                  # 删除数据集

# 数据清洗
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/missing    # 缺失值处理
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/outlier    # 异常值检测
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/dedup      # 去重
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/encode     # 编码转换
POST   /api/v1/projects/{id}/datasets/{ds_id}/clean/type-convert  # 类型转换

# EDA
POST   /api/v1/projects/{id}/datasets/{ds_id}/eda              # 触发一键 EDA
GET    /api/v1/projects/{id}/datasets/{ds_id}/eda/report       # 获取 EDA 报告

# 数据增强 & 划分
POST   /api/v1/projects/{id}/datasets/{ds_id}/augment          # CV 数据增强
POST   /api/v1/projects/{id}/datasets/{ds_id}/split            # 数据集划分
```

## 接口请求/响应要点

- 分页接口统一响应：`{ code, message, data: { page, page_size, total, items[] } }`
- 文件上传流程：先调 `upload/init` 获取 `upload_id` → 循环调 `upload/{uid}/chunk` 上传分片（带 `Content-Range` header）→ 调 `upload/{uid}/complete` 合并
- 清洗操作请求体示例：`{ "strategy": "fill_mean", "columns": ["age", "income"] }`
- EDA 报告响应包含统计量 + 图表数据（前端用 ECharts 渲染）
- 错误码格式 `30-XX-YYY`（30 = 数据集模块）

## 技术栈

React 18, TypeScript, Ant Design 5.x, Zustand, React Query, ECharts (echarts-for-react), MSW

## 你使用的通用组件（P2 提供）

- `<FileUpload>` — 拖拽上传 + 分片 + 进度条
- `<DataTable>` — 分页表格，内置搜索和筛选

## 开发顺序建议

1. Day1：用 MSW mock 数据完成上传页 + 数据集列表页骨架
2. Day2：接入真实上传 API + 预览页 + 图片画廊页（mock）
3. Day2 下午：清洗操作页 + EDA 报告页骨架
4. Day3：切换 MSW → 真实 API，联调
5. Day3-4：数据增强页 + UI 打磨
