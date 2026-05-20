"""ChatMessage — individual message in a conversation."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.protocols import ChatRole
from src.infra.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.infra.db.types import JSONType

if TYPE_CHECKING:
    pass


class ChatMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[ChatRole] = mapped_column(
        Enum(ChatRole, name="chat_role", native_enum=False),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[Optional[list]] = mapped_column(JSONType, nullable=True)
    tool_call_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
