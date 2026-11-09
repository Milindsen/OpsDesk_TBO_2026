import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.user import User

class TicketComment(Base):
    __tablename__ = "ticket_comments"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="internal")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (Index("ix_ticket_comments_ticket_created", "ticket_id", "created_at"),)
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="comments")
    author: Mapped[Optional["User"]] = relationship("User")
