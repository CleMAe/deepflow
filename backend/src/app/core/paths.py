"""Resolve monorepo `src/shared` for Protocol imports."""

from __future__ import annotations

import sys
from pathlib import Path


def setup_protocol_path() -> Path | None:
    """Add `deepflow/src` to sys.path when present (local or monorepo layout)."""
    app_dir = Path(__file__).resolve().parents[1]  # .../app
    candidates = [
        app_dir.parents[3] / "src",  # deepflow/backend/src/app → deepflow/src
        app_dir.parents[4] / "deepflow" / "src",  # hezuo01/backend layout (local dev)
    ]
    for path in candidates:
        if (path / "shared" / "protocols.py").is_file():
            root = str(path)
            if root not in sys.path:
                sys.path.insert(0, root)
            return path
    return None
