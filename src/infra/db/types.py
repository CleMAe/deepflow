"""Cross-dialect column types (PostgreSQL JSONB + SQLite JSON)."""

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

JSONType = JSON().with_variant(JSONB(), "postgresql")
