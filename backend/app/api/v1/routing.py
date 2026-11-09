from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.routing_log import RoutingLog
from app.models.ticket import Ticket
from app.models.timeline import TimelineEvent
from app.models.user import User
from app.schemas.routing import AutoRouteResponse, CandidateScore
from app.services.routing_engine import route_ticket

router = APIRouter(prefix="/routing", tags=["routing"])


@router.post("/auto-route/{ticket_id}", response_model=AutoRouteResponse)
def auto_route_ticket(
    ticket_id: UUID,
    current_user: User = Depends(require_role("agent", "lead", "escalation_manager")),
    db: Session = Depends(get_db),
) -> AutoRouteResponse:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    now = datetime.now(timezone.utc)
    chosen_agent, candidate_scores, routing_reason = route_ticket(db, ticket, now=now)

    if chosen_agent:
        old_assignee_id = ticket.assignee_id
        ticket.assignee_id = chosen_agent.id
        ticket.routing_reason = routing_reason
        is_active_ticket = ticket.status not in {"Resolved", "Closed"}
        if is_active_ticket and old_assignee_id != chosen_agent.id:
            chosen_agent.current_load = (chosen_agent.current_load or 0) + 1

        if is_active_ticket and old_assignee_id and old_assignee_id != chosen_agent.id:
            old_agent = db.get(User, old_assignee_id)
            if old_agent and old_agent.current_load > 0:
                old_agent.current_load -= 1

        log_entry = RoutingLog(
            ticket_id=ticket.id,
            chosen_agent_id=chosen_agent.id,
            candidate_scores=candidate_scores,
            reason_text=routing_reason,
            routed_at=now,
        )
        db.add(log_entry)

        event = TimelineEvent(
            ticket_id=ticket.id,
            actor_id=current_user.id,
            actor_name=current_user.full_name,
            event_type="assignment",
            payload={
                "assigned_to": str(chosen_agent.id),
                "agent_name": chosen_agent.full_name,
                "reason": routing_reason,
                "manual_trigger": True,
            },
            created_at=now,
        )
        db.add(event)

        db.commit()
        db.refresh(ticket)
    else:
        old_assignee_id = ticket.assignee_id
        if old_assignee_id and ticket.status not in {"Resolved", "Closed"}:
            old_agent = db.get(User, old_assignee_id)
            if old_agent and old_agent.current_load > 0:
                old_agent.current_load -= 1
        ticket.assignee_id = None
        ticket.routing_reason = routing_reason
        ticket.updated_at = now
        db.add(RoutingLog(
            ticket_id=ticket.id,
            chosen_agent_id=None,
            candidate_scores=candidate_scores,
            reason_text=routing_reason,
            routed_at=now,
        ))
        db.add(TimelineEvent(ticket_id=ticket.id, actor_id=current_user.id, actor_name=current_user.full_name,
            event_type="routing_unassigned", payload={"reason":routing_reason, "previous_assignee_id":str(old_assignee_id) if old_assignee_id else None}, created_at=now))
        db.commit()
        db.refresh(ticket)

    parsed_scores = [
        CandidateScore(
            agent_id=s["agent_id"],
            name=s["name"],
            score=s["score"],
            breakdown=s["breakdown"],
        )
        for s in candidate_scores
    ]

    return AutoRouteResponse(
        ticket_id=ticket.id,
        chosen_agent_id=chosen_agent.id if chosen_agent else None,
        chosen_agent_name=chosen_agent.full_name if chosen_agent else None,
        scores=parsed_scores,
        reason=routing_reason,
    )
