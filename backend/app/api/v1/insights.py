from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.theme import Theme, TicketTheme
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.insights import (
    IntentScore,
    IntentSuggestRequest,
    ThemeInsightResponse,
    ThemeSampleTicket,
)
from app.services.intent_classifier import get_intent_classifier

router = APIRouter(tags=["insights"])


@router.get("/insights/themes", response_model=List[ThemeInsightResponse])
def get_theme_insights(
    since: Optional[datetime] = None,
    current_user: User = Depends(require_role("lead")),
    db: Session = Depends(get_db),
) -> List[ThemeInsightResponse]:
    if since is None:
        since = datetime.now(timezone.utc) - timedelta(days=7)

    themes = db.scalars(select(Theme)).all()
    results: List[ThemeInsightResponse] = []

    for th in themes:
        # Count tickets with recent activity for this theme since the requested period
        q = (
            select(Ticket)
            .join(TicketTheme, TicketTheme.ticket_id == Ticket.id)
            .where(
                TicketTheme.theme_id == th.id,
                Ticket.updated_at >= since,
            )
        )
        count = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        samples = db.scalars(q.order_by(desc(Ticket.updated_at)).limit(5)).all()

        sample_tickets = [
            ThemeSampleTicket(
                id=s.id,
                title=s.title,
                tboh=s.tboh,
                priority=s.priority,
                status=s.status,
                created_at=s.created_at,
                agency_id=s.agency_id,
                agency_name=s.agency.name if s.agency else "Unknown agency",
            )
            for s in samples
        ]

        results.append(
            ThemeInsightResponse(
                theme_name=th.name,
                count=count,
                sample_tickets=sample_tickets,
            )
        )

    results.sort(key=lambda x: x.count, reverse=True)
    return results


@router.post("/intent/suggest", response_model=List[IntentScore])
def suggest_intent(
    req: IntentSuggestRequest,
    current_user: User = Depends(require_role("requester", "agent", "lead", "escalation_manager")),
) -> List[IntentScore]:
    classifier = get_intent_classifier()
    results = classifier.suggest(req.title, req.description)
    return [IntentScore(intent=r["intent"], confidence=r["confidence"]) for r in results]
