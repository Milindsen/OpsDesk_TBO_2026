import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.ticket import Ticket


class TicketLink(Base):
    __tablename__ = "ticket_links"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    link_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_ticket_links_source_target", "source_id", "target_id"),
    )

    source_ticket: Mapped["Ticket"] = relationship(
        "Ticket",
        foreign_keys=[source_id],
        back_populates="links_as_source",
    )
    target_ticket: Mapped["Ticket"] = relationship(
        "Ticket",
        foreign_keys=[target_id],
        back_populates="links_as_target",
    )
