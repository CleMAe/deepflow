"""PromptTemplate — reusable prompt with $variable substitution."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.db.base import Base, TimestampUpdateMixin, UUIDPrimaryKeyMixin
from src.infra.db.types import JSONType

if TYPE_CHECKING:
    from src.infra.db.models.agent import Agent


class PromptTemplate(UUIDPrimaryKeyMixin, TimestampUpdateMixin, Base):
    __tablename__ = "prompt_templates"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    variables: Mapped[Optional[list]] = mapped_column(JSONType, nullable=True)

    agent: Mapped["Agent"] = relationship(back_populates="prompt_templates")
