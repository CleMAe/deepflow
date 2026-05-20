"""App-layer config bridge.

This module only re-exports the canonical infra settings for legacy imports.
Do not add independent app-layer settings here; shared backend configuration
is maintained in `src.infra.config`.
"""

from __future__ import annotations

# Re-export the canonical infra settings so existing imports keep working.
from src.infra.config import settings  # noqa: F401
