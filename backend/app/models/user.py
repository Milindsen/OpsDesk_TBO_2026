import uuid
from datetime import datetime, time, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Time, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.agency import Agency
    from app.models.ticket import Ticket


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    region: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    agency_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("agencies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    shift_start: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
    )
    shift_end: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
    )
    availability: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    current_load: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    agency: Mapped[Optional["Agency"]] = relationship(
        "Agency",
        back_populates="users",
    )
    assigned_tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket",
        back_populates="assignee",
        foreign_keys="Ticket.assignee_id",
    )
