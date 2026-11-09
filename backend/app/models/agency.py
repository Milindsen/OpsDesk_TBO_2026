import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.user import User


class Agency(Base):
    __tablename__ = "agencies"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    region: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="agency",
        cascade="all, delete-orphan",
    )
    tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket",
        back_populates="agency",
        cascade="all, delete-orphan",
    )
