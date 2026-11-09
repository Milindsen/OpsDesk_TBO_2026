import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.user import User


class RoutingLog(Base):
    __tablename__ = "routing_log"

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
    chosen_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    candidate_scores: Mapped[List[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    reason_text: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    routed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_routing_log_ticket_routed", "ticket_id", "routed_at"),
    )

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="routing_logs")
    chosen_agent: Mapped[Optional["User"]] = relationship("User")
