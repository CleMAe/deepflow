#!/usr/bin/env bash
# DeepFlow GPU environment verification (run on cloud GPU host)
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

ok() { echo -e "${GREEN}[OK]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*" >&2; exit 1; }

echo "=== 1. NVIDIA driver ==="
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi
  ok "nvidia-smi available"
else
  fail "nvidia-smi not found — install NVIDIA driver first"
fi

echo ""
echo "=== 2. Docker NVIDIA runtime ==="
if command -v docker >/dev/null 2>&1; then
  docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi \
    && ok "Docker GPU passthrough works" \
    || fail "Docker --gpus all failed — install nvidia-container-toolkit"
else
  echo "Docker not installed — skip container GPU check"
fi

echo ""
echo "=== 3. PyTorch CUDA (host or venv) ==="
python3 - <<'PY' || fail "PyTorch CUDA check failed"
import json
import sys

try:
    import torch
except ImportError:
    print("PyTorch not installed in current Python", file=sys.stderr)
    sys.exit(1)

info = {
    "torch_version": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "cuda_version": torch.version.cuda,
    "device_count": torch.cuda.device_count(),
}
if info["cuda_available"]:
    info["device_0"] = torch.cuda.get_device_name(0)
    x = torch.randn(4, 4, device="cuda")
    info["matmul_ok"] = bool((x @ x).sum().item())

print(json.dumps(info, indent=2))
if not info["cuda_available"]:
    sys.exit(2)
PY

ok "PyTorch sees CUDA"

echo ""
echo "=== 4. DeepFlow gpu-train image (optional) ==="
if command -v docker >/dev/null 2>&1 && [ -f docker-compose.yml ]; then
  docker compose --profile gpu build gpu-train
  docker compose --profile gpu run --rm gpu-train python -c "import torch; print(torch.cuda.is_available())"
  ok "gpu-train compose service OK"
fi

echo ""
ok "All GPU checks passed"
