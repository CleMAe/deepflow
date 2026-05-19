"""Initial core tables — users, projects, datasets, models, training_jobs, agents, experiments.

Revision ID: 001_initial
Revises:
Create Date: 2026-05-19

Frozen per DeepFlow DDL spec (section 4.2) and openapi.yaml schemas.

Enum columns use ``native_enum=False`` (VARCHAR + CHECK constraint). PostgreSQL
does not create named ENUM types, so ``downgrade()`` only drops tables.

If you later switch to ``native_enum=True``, extend ``downgrade()`` after
``drop_table`` with::

    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("DROP TYPE IF EXISTS dataset_format")
    op.execute("DROP TYPE IF EXISTS dataset_status")
    op.execute("DROP TYPE IF EXISTS training_job_status")
    op.execute("DROP TYPE IF EXISTS agent_status")
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSON = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(32), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "developer", "viewer", name="user_role", native_enum=False),
            nullable=False,
            server_default="developer",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_quota", sa.Integer(), nullable=False, server_default="10240"),
        sa.Column("storage_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])

    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("project_id", sa.Uuid(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "format",
            sa.Enum("csv", "json", "image", "other", name="dataset_format", native_enum=False),
            nullable=False,
            server_default="other",
        ),
        sa.Column("file_path", sa.String(1024), nullable=True),
        sa.Column("num_samples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("num_columns", sa.Integer(), nullable=True),
        sa.Column("columns_meta", JSON, nullable=True),
        sa.Column("tags", JSON, nullable=True),
        sa.Column(
            "status",
            sa.Enum("uploading", "ready", "cleaning", "cleaned", "error", name="dataset_status", native_enum=False),
            nullable=False,
            server_default="uploading",
        ),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_datasets_project_id", "datasets", ["project_id"])

    op.create_table(
        "models",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("project_id", sa.Uuid(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("arch_type", sa.String(64), nullable=False),
        sa.Column("params_cfg", JSON, nullable=True),
        sa.Column("pretrained", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("pretrained_source", sa.String(256), nullable=True),
        sa.Column("model_path", sa.String(1024), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_models_project_id", "models", ["project_id"])

    op.create_table(
        "training_jobs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("project_id", sa.Uuid(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("model_id", sa.Uuid(as_uuid=True), sa.ForeignKey("models.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("dataset_id", sa.Uuid(as_uuid=True), sa.ForeignKey("datasets.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("val_dataset_id", sa.Uuid(as_uuid=True), sa.ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("hyperparams", JSON, nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "running", "paused", "success", "failed", "cancelled",
                name="training_job_status",
                native_enum=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("device", sa.String(32), nullable=True, server_default="auto"),
        sa.Column("current_epoch", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_epochs", sa.Integer(), nullable=True),
        sa.Column("metrics", JSON, nullable=True),
        sa.Column("checkpoint", sa.String(1024), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_training_jobs_project_id", "training_jobs", ["project_id"])
    op.create_index("ix_training_jobs_model_id", "training_jobs", ["model_id"])
    op.create_index("ix_training_jobs_dataset_id", "training_jobs", ["dataset_id"])
    op.create_index("ix_training_jobs_status", "training_jobs", ["status"])

    op.create_table(
        "agents",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("project_id", sa.Uuid(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("model_config", JSON, nullable=True),
        sa.Column("tools", JSON, nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "inactive", name="agent_status", native_enum=False),
            nullable=False,
            server_default="active",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agents_project_id", "agents", ["project_id"])

    op.create_table(
        "experiments",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("project_id", sa.Uuid(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Uuid(as_uuid=True), sa.ForeignKey("training_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(256), nullable=True),
        sa.Column("metrics", JSON, nullable=True),
        sa.Column("params_snap", JSON, nullable=True),
        sa.Column("tags", JSON, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_experiments_project_id", "experiments", ["project_id"])
    op.create_index("ix_experiments_job_id", "experiments", ["job_id"])


def downgrade() -> None:
    # See module docstring: native_enum=False needs no DROP TYPE; add those if
    # migrations are regenerated with native_enum=True.
    op.drop_table("experiments")
    op.drop_table("agents")
    op.drop_table("training_jobs")
    op.drop_table("models")
    op.drop_table("datasets")
    op.drop_table("projects")
    op.drop_table("users")
