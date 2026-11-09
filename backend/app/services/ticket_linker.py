from typing import Any, List
from uuid import UUID
from datetime import timezone

from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.ticket_link import TicketLink


def _as_utc(dt: Any):
    """Ensure datetime is timezone-aware (UTC). Convert naive datetimes."""
    if dt is None:
        return None
    if hasattr(dt, 'tzinfo') and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class LinkCandidate(BaseModel):
    target_id: UUID
    link_type: str  # strong, medium, weak
    reason: str
    score: float


def find_links(new_ticket: Any, existing_tickets: List[Any]) -> List[LinkCandidate]:
    links: List[LinkCandidate] = []
    seen_targets = set()

    for t in existing_tickets:
        if getattr(t, "id", None) == getattr(new_ticket, "id", None):
            continue
        target_id = getattr(t, "id", None)
        if not target_id or target_id in seen_targets:
            continue

        days_diff = 99999
        if getattr(new_ticket, "created_at", None) and getattr(t, "created_at", None):
            days_diff = abs((_as_utc(new_ticket.created_at) - _as_utc(t.created_at)).total_seconds()) / 86400.0

        if getattr(t, "tboh", None) and getattr(t, "tboh", "") == getattr(new_ticket, "tboh", ""):
            links.append(
                LinkCandidate(
                    target_id=target_id,
                    link_type="strong",
                    reason=f"Same TBOH: {t.tboh}",
                    score=1.0,
                )
            )
            seen_targets.add(target_id)
        elif (
            getattr(t, "agency_id", None) == getattr(new_ticket, "agency_id", None)
            and getattr(t, "intent", None) == getattr(new_ticket, "intent", None)
            and days_diff <= 30
        ):
            links.append(
                LinkCandidate(
                    target_id=target_id,
                    link_type="medium",
                    reason="Same agency + intent within 30 days",
                    score=0.7,
                )
            )
            seen_targets.add(target_id)
        elif (
            getattr(t, "agency_id", None) == getattr(new_ticket, "agency_id", None)
            and days_diff <= 7
        ):
            links.append(
                LinkCandidate(
                    target_id=target_id,
                    link_type="weak",
                    reason="Same agency within 7 days",
                    score=0.4,
                )
            )
            seen_targets.add(target_id)

    # Sort by score descending
    links.sort(key=lambda x: x.score, reverse=True)
    return links


def link_ticket(db: Session, ticket: Ticket) -> List[TicketLink]:
    # Query candidates matching agency or TBOH
    conditions = [Ticket.agency_id == ticket.agency_id]
    if ticket.tboh:
        conditions.append(Ticket.tboh == ticket.tboh)

    existing = db.scalars(
        select(Ticket).where(
            Ticket.id != ticket.id,
            or_(*conditions),
        )
    ).all()

    candidates = find_links(ticket, list(existing))
    created_links: List[TicketLink] = []

    for c in candidates:
        link = TicketLink(
            source_id=ticket.id,
            target_id=c.target_id,
            link_type=c.link_type,
            reason=c.reason,
            score=c.score,
        )
        db.add(link)
        created_links.append(link)

    return created_links
