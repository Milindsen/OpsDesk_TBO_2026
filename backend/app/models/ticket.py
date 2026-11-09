import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.comment import TicketComment
    from app.models.agency import Agency
    from app.models.escalation import Escalation
    from app.models.routing_log import RoutingLog
    from app.models.side_conversation import SideConversation
    from app.models.theme import TicketTheme
    from app.models.ticket_link import TicketLink
    from app.models.timeline import TimelineEvent
    from app.models.user import User


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    agency_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("agencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    tboh: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    priority: Mapped[str] = mapped_column(
        String(10),
        default="P3",
        nullable=False,
    )
    intent: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="New",
        nullable=False,
    )
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    region: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    check_in_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    lcd: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    sla_due: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    sla_status: Mapped[str] = mapped_column(
        String(20),
        default="ok",
        nullable=False,
    )
    routing_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    contact_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    product_bug_link: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_tickets_created_at", "created_at"),
    )

    agency: Mapped["Agency"] = relationship("Agency", back_populates="tickets")
    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="assigned_tickets",
        foreign_keys=[assignee_id],
    )
    links_as_source: Mapped[List["TicketLink"]] = relationship(
        "TicketLink",
        foreign_keys="TicketLink.source_id",
        back_populates="source_ticket",
        cascade="all, delete-orphan",
    )
    links_as_target: Mapped[List["TicketLink"]] = relationship(
        "TicketLink",
        foreign_keys="TicketLink.target_id",
        back_populates="target_ticket",
        cascade="all, delete-orphan",
    )
    timeline_events: Mapped[List["TimelineEvent"]] = relationship(
        "TimelineEvent",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="desc(TimelineEvent.created_at)",
    )
    routing_logs: Mapped[List["RoutingLog"]] = relationship(
        "RoutingLog",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
    side_conversations: Mapped[List["SideConversation"]] = relationship(
        "SideConversation",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
    themes: Mapped[List["TicketTheme"]] = relationship(
        "TicketTheme",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
    escalation: Mapped[Optional["Escalation"]] = relationship(
        "Escalation",
        back_populates="ticket",
        uselist=False,
        cascade="all, delete-orphan",
    )
    comments: Mapped[List["TicketComment"]] = relationship(
        "TicketComment", back_populates="ticket", cascade="all, delete-orphan",
        order_by="TicketComment.created_at",
    )

