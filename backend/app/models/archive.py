import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Date, DateTime, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ArchivedTicket(Base):
    __tablename__ = "archived_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
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
        nullable=False,
    )
    tboh: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    priority: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    intent: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
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
    product_bug_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    archived_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    archive_reason: Mapped[str] = mapped_column(
        String(100),
        default="auto_90d",
        nullable=False,
    )
    timeline_snapshot: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    links_snapshot: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    side_conversations_snapshot: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    routing_logs_snapshot: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    themes_snapshot: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    escalation_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    comments_snapshot: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    __table_args__ = (
        Index("ix_arch_tickets_tboh", "tboh"),
        Index("ix_arch_tickets_agency_id", "agency_id"),
        Index("ix_arch_tickets_assignee_id", "assignee_id"),
        Index("ix_arch_tickets_archived_at", "archived_at"),
    )
