import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.user import User


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    escalated_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    escalated_to_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    escalated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    __table_args__ = (
        Index("ix_escalations_ticket_id", "ticket_id"),
        Index("ix_escalations_escalated_to", "escalated_to_id"),
    )

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="escalation")
    escalated_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[escalated_by_id],
    )
    escalated_to: Mapped["User"] = relationship(
        "User",
        foreign_keys=[escalated_to_id],
    )
