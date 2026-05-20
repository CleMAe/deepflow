"""AgentTool — binds a model/API tool to an Agent for function calling."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.db.base import Base, TimestampUpdateMixin, UUIDPrimaryKeyMixin
from src.infra.db.types import JSONType
from shared.protocols import ToolType

if TYPE_CHECKING:
    from src.infra.db.models.agent import Agent


class AgentTool(UUIDPrimaryKeyMixin, TimestampUpdateMixin, Base):
    __tablename__ = "agent_tools"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[ToolType] = mapped_column(
        Enum(ToolType, name="tool_type", native_enum=False),
        nullable=False,
        default=ToolType.MODEL_INFERENCE,
    )
    model_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)

    agent: Mapped["Agent"] = relationship(back_populates="agent_tools")
