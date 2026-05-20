"""Conversation — groups chat messages for an Agent session."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.db.base import Base, TimestampUpdateMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.infra.db.models.agent import Agent
    from src.infra.db.models.project import Project


class Conversation(UUIDPrimaryKeyMixin, TimestampUpdateMixin, Base):
    __tablename__ = "conversations"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    agent: Mapped["Agent"] = relationship(back_populates="conversations")
