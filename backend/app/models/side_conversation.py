import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.user import User


class SideConversation(Base):
    __tablename__ = "side_conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(
        String(20),
        default="supplier",
        nullable=False,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="side_conversations")
    created_by: Mapped["User"] = relationship("User")
    recipients: Mapped[List["SideRecipient"]] = relationship(
        "SideRecipient",
        back_populates="side_conversation",
        cascade="all, delete-orphan",
    )
    messages: Mapped[List["SideMessage"]] = relationship(
        "SideMessage",
        back_populates="side_conversation",
        cascade="all, delete-orphan",
        order_by="SideMessage.sent_at",
    )


class SideRecipient(Base):
    __tablename__ = "side_recipients"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    side_conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("side_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    side_conversation: Mapped["SideConversation"] = relationship(
        "SideConversation",
        back_populates="recipients",
    )


class SideMessage(Base):
    __tablename__ = "side_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    side_conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("side_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    author_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(
        String(20),
        default="external",
        nullable=False,
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_side_messages_convo_sent", "side_conversation_id", "sent_at"),
    )

    side_conversation: Mapped["SideConversation"] = relationship(
        "SideConversation",
        back_populates="messages",
    )
    author: Mapped[Optional["User"]] = relationship("User")
