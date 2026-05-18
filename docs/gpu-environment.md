# DeepFlow GPU 环境验证指南

在云端 GPU 服务器上部署训练引擎前，按下列步骤确认 CUDA + PyTorch 可用。

## 前置条件

| 组件 | 版本建议 |
|------|----------|
| NVIDIA Driver | ≥ 525（与 CUDA 12.1 兼容） |
| CUDA Toolkit | 12.1（与 `gpu-train` 镜像一致） |
| Docker | 24+ |
| NVIDIA Container Toolkit | 最新稳定版 |

安装 NVIDIA Container Toolkit 后重启 Docker：

```bash
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## 一键验证

```bash
chmod +x scripts/verify_gpu.sh
./scripts/verify_gpu.sh
```

脚本依次检查：

1. `nvidia-smi` — 宿主机驱动
2. `docker run --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi` — 容器 GPU 透传
3. 当前 Python 环境中 `torch.cuda.is_available()` 与简单矩阵运算
4. （可选）`docker compose --profile gpu` 启动 `gpu-train` 服务

## 手动检查命令

```bash
# 宿主机
nvidia-smi

# Docker GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# PyTorch
python3 -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

## Compose 启动 GPU 训练容器

```bash
# 仅 app + db（Day 1 默认）
docker compose up -d db backend frontend

# 含 GPU 训练 worker（需 NVIDIA runtime）
docker compose --profile gpu up -d gpu-train
```

## 常见问题

| 现象 | 处理 |
|------|------|
| `could not select device driver` | 安装并配置 `nvidia-container-toolkit` |
| `CUDA available: False` 于容器内 | 确认 `runtime: nvidia` 或 Compose `deploy.resources.reservations.devices` |
| 驱动版本过低 | 升级宿主机 NVIDIA 驱动以匹配 CUDA 12.1 |

## 与训练引擎的关系

- **Day 1**：`gpu-train` 容器仅验证 PyTorch CUDA 通路，进程 idle。
- **Day 2+**：P8 将训练子进程/引擎挂载到该服务，使用 `scripts/gen_synthetic_data.py --preset fast-epoch` 做 5 秒 epoch 冒烟。
