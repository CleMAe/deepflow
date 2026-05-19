#!/usr/bin/env bash
set -euo pipefail

echo "=== DeepFlow gpu-train container ==="
python - <<'PY'
import json
import sys

try:
    import torch
except ImportError:
    print("PyTorch not installed", file=sys.stderr)
    sys.exit(1)

info = {
    "torch_version": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "cuda_device_count": torch.cuda.device_count(),
}
if torch.cuda.is_available():
    info["cuda_device_name"] = torch.cuda.get_device_name(0)

print(json.dumps(info, indent=2))
if not info["cuda_available"]:
    print("WARNING: CUDA not available — training will fall back to CPU.", file=sys.stderr)
PY

# Day 1: idle worker; P8 mounts training engine and job queue later
exec tail -f /dev/null
