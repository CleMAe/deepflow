"""Agent model — LLM agent configuration & tools."""

from typing import TYPE_CHECKING, Optional

import enum

from sqlalchemy import Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.db.base import Base, TimestampUpdateMixin, UUIDPrimaryKeyMixin
from src.infra.db.types import JSONType

if TYPE_CHECKING:
    from src.infra.db.models.project import Project


class AgentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Agent(UUIDPrimaryKeyMixin, TimestampUpdateMixin, Base):
    __tablename__ = "agents"

    project_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_config: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    tools: Mapped[Optional[list]] = mapped_column(JSONType, nullable=True)
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, name="agent_status", native_enum=False),
        nullable=False,
        default=AgentStatus.ACTIVE,
    )

    project: Mapped["Project"] = relationship(back_populates="agents")
