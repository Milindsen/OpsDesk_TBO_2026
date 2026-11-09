import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Float, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.ticket import Ticket


class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    ticket_themes: Mapped[List["TicketTheme"]] = relationship(
        "TicketTheme",
        back_populates="theme",
        cascade="all, delete-orphan",
    )


class TicketTheme(Base):
    __tablename__ = "ticket_themes"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    theme_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("themes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_ticket_themes_theme_id", "theme_id"),
    )

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="themes")
    theme: Mapped["Theme"] = relationship("Theme", back_populates="ticket_themes")
