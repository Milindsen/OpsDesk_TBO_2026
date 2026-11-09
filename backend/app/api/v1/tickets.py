from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.database import get_db
from app.dependencies import agency_ticket_guard, get_current_user, require_role
from app.models.comment import TicketComment
from app.models.agency import Agency
from app.models.escalation import Escalation
from app.models.routing_log import RoutingLog
from app.models.ticket import Ticket
from app.models.ticket_link import TicketLink
from app.models.timeline import TimelineEvent
from app.models.user import User
from app.schemas.ticket import (
    EscalationResponse,
    LinkResponse,
    TicketAssignRequest,
    TicketCreate,
    TicketDetailResponse,
    TicketEscalateRequest,
    TicketListResponse,
    TicketResponse,
    TicketTransitionRequest,
    TicketUpdate,
    TimelineResponse,
)
from app.schemas.comment import TicketCommentCreate, TicketCommentResponse
from app.services.intent_classifier import get_intent_classifier
from app.services.routing_engine import route_ticket
from app.services.sla_engine import compute_sla_due, compute_sla_status
from app.services.theme_tagger import apply_theme_tags
from app.services.theme_tagger import apply_theme_tags
from app.services.ticket_linker import link_ticket

router = APIRouter(prefix="/tickets", tags=["tickets"])

VALID_TRANSITIONS = {
    "New": ["Open"],
    "Open": ["Pending", "Escalated", "Resolved"],
    "Pending": ["Open", "Resolved"],
    "Escalated": ["Resolved", "Open"],
    "Resolved": ["Closed"],
    "Closed": [],
}


def _timeline_visible_to_requester(event: TimelineEvent) -> bool:
    """Only expose customer-safe events in requester-facing case history."""
    if event.event_type == "ticket_comment":
        return (event.payload or {}).get("visibility") == "public"
    return event.event_type == "status_change"


def _timeline_response(event: TimelineEvent, requester_view: bool = False) -> TimelineResponse:
    response = TimelineResponse.model_validate(event)
    if requester_view and event.event_type == "status_change":
        # Status-transition notes are staff-entered operational context, not public replies.
        response.payload = {key: value for key, value in (event.payload or {}).items() if key in {"from", "to"}}
    return response


@router.get("", response_model=TicketListResponse)
def list_tickets(
    status_filter: Optional[str] = Query(None, alias="status"),
    intent: Optional[str] = None,
    region: Optional[str] = None,
    priority: Optional[str] = None,
    has_links: Optional[bool] = None,
    assignee_id: Optional[UUID] = None,
    agency_id: Optional[UUID] = None,
    tboh: Optional[str] = None,
    unassigned: Optional[bool] = None,
    escalated: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketListResponse:
    query = select(Ticket)

    # RBAC: requesters can only see tickets from their own agency
    if current_user.role == "requester":
        if not current_user.agency_id:
            return TicketListResponse(items=[], total=0, page=page, page_size=page_size)
        query = query.where(Ticket.agency_id == current_user.agency_id)
    elif current_user.role == "escalation_manager":
        query = query.where(Ticket.assignee_id == current_user.id)
    elif agency_id:
        query = query.where(Ticket.agency_id == agency_id)

    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if intent:
        query = query.where(Ticket.intent == intent)
    if region:
        query = query.where(Ticket.region == region)
    if priority:
        query = query.where(Ticket.priority == priority)
    if has_links is not None:
        link_query = select(TicketLink.id).where(
            TicketLink.link_type.in_(["strong", "medium", "weak"]),
            or_(TicketLink.source_id == Ticket.id, TicketLink.target_id == Ticket.id),
        )
        if current_user.role == "requester":
            linked_ticket = aliased(Ticket)
            link_query = (
                select(TicketLink.id)
                .join(
                    linked_ticket,
                    or_(
                        and_(TicketLink.source_id == Ticket.id, TicketLink.target_id == linked_ticket.id),
                        and_(TicketLink.target_id == Ticket.id, TicketLink.source_id == linked_ticket.id),
                    ),
                )
                .where(
                    TicketLink.link_type.in_(["strong", "medium", "weak"]),
                    linked_ticket.agency_id == current_user.agency_id,
                )
            )
        query = query.where(link_query.exists() if has_links else ~link_query.exists())
    if assignee_id:
        query = query.where(Ticket.assignee_id == assignee_id)
    if tboh:
        query = query.where(Ticket.tboh == tboh)
    if unassigned is True:
        query = query.where(Ticket.assignee_id.is_(None))
    elif unassigned is False:
        query = query.where(Ticket.assignee_id.is_not(None))
    if escalated is True:
        query = query.where(Ticket.status == "Escalated")

    # Count total
    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_stmt) or 0

    # Sorting
    if sort_by == "priority":
        query = query.order_by(Ticket.priority.asc(), Ticket.created_at.desc())
    elif sort_by == "sla_due":
        query = query.order_by(Ticket.sla_due.asc().nullslast())
    else:
        query = query.order_by(desc(Ticket.created_at))

    # Pagination
    offset = (page - 1) * page_size
    tickets = db.scalars(query.offset(offset).limit(page_size)).all()

    items = []
    sla_changed = False
    now = datetime.now(timezone.utc)
    for t in tickets:
        if t.sla_due:
            refreshed_sla_status = compute_sla_status(
                sla_due=t.sla_due,
                now=now,
                created_at=t.created_at,
            )
            if refreshed_sla_status != t.sla_status:
                t.sla_status = refreshed_sla_status
                sla_changed = True
        item = TicketResponse.model_validate(t)
        if t.agency:
            item.agency_name = t.agency.name
        if t.assignee:
            item.assignee_name = t.assignee.full_name
        if current_user.role == "requester":
            item.routing_reason = None
            item.product_bug_link = None
        items.append(item)
    if sla_changed:
        db.commit()
    return TicketListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_in: TicketCreate,
    current_user: User = Depends(require_role("requester", "agent", "lead")),
    db: Session = Depends(get_db),
) -> TicketResponse:
    # Resolve agency_id
    if current_user.role == "requester":
        if not current_user.agency_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requester has no associated agency",
            )
        resolved_agency_id = current_user.agency_id
    else:
        if not ticket_in.agency_id:
            # Auto-pick first available agency for agents/leads/EMs
            from app.models.agency import Agency as AgencyModel
            first_agency = db.scalars(select(AgencyModel).limit(1)).first()
            if not first_agency:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No agencies found in system",
                )
            resolved_agency_id = first_agency.id
        else:
            resolved_agency_id = ticket_in.agency_id if isinstance(ticket_in.agency_id, UUID) else UUID(str(ticket_in.agency_id))

    agency = db.get(Agency, resolved_agency_id if isinstance(resolved_agency_id, UUID) else UUID(str(resolved_agency_id)))
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency not found",
        )

    # Resolve region
    resolved_region = agency.region if current_user.role == "requester" else (ticket_in.region or agency.region)

    # Resolve intent if not provided
    resolved_intent = ticket_in.intent
    if not resolved_intent:
        classifier = get_intent_classifier()
        suggestions = classifier.suggest(ticket_in.title, ticket_in.description)
        resolved_intent = suggestions[0]["intent"] if suggestions else "other"

    now = datetime.now(timezone.utc)

    # Compute contact_count (how many times this agency contacted about this TBOH/intent)
    prev_count = db.scalar(
        select(func.count(Ticket.id)).where(
            Ticket.agency_id == resolved_agency_id,
            Ticket.tboh == ticket_in.tboh,
            Ticket.intent == resolved_intent,
        )
    ) or 0
    contact_count = prev_count + 1

    # Compute SLA
    sla_due = compute_sla_due(
        priority=ticket_in.priority,
        created_at=now,
        check_in_date=ticket_in.check_in_date,
        lcd=ticket_in.lcd,
    )
    sla_status = compute_sla_status(sla_due=sla_due, now=now, created_at=now)

    ticket = Ticket(
        title=ticket_in.title,
        description=ticket_in.description,
        agency_id=resolved_agency_id,
        tboh=ticket_in.tboh,
        priority=ticket_in.priority,
        intent=resolved_intent,
        status="New",
        region=resolved_region,
        check_in_date=ticket_in.check_in_date,
        lcd=ticket_in.lcd,
        sla_due=sla_due,
        sla_status=sla_status,
        contact_count=contact_count,
        created_at=now,
        updated_at=now,
    )
    db.add(ticket)
    db.flush()

    # Auto-linking: links are first-class records and also visible in the activity timeline.
    created_links = link_ticket(db, ticket)
    for link in created_links:
        linked_ticket = db.get(Ticket, link.target_id)
        db.add(TimelineEvent(
            ticket_id=ticket.id,
            actor_id=None,
            actor_name="System Linker",
            event_type="ticket_link",
            payload={
                "target_ticket_id": str(link.target_id),
                "target_title": linked_ticket.title if linked_ticket else "Linked ticket",
                "link_type": link.link_type,
                "reason": link.reason,
                "score": link.score,
            },
            created_at=now,
        ))

    # Auto-routing
    chosen_agent, candidate_scores, routing_reason = route_ticket(db, ticket, now=now)
    if chosen_agent:
        ticket.assignee_id = chosen_agent.id
        ticket.routing_reason = routing_reason
        chosen_agent.current_load = (chosen_agent.current_load or 0) + 1

        routing_log = RoutingLog(
            ticket_id=ticket.id,
            chosen_agent_id=chosen_agent.id,
            candidate_scores=candidate_scores,
            reason_text=routing_reason,
            routed_at=now,
        )
        db.add(routing_log)
    else:
        ticket.assignee_id = None
        ticket.routing_reason = routing_reason
        db.add(RoutingLog(
            ticket_id=ticket.id,
            chosen_agent_id=None,
            candidate_scores=candidate_scores,
            reason_text=routing_reason,
            routed_at=now,
        ))
        db.add(TimelineEvent(
            ticket_id=ticket.id,
            actor_id=None,
            actor_name="System Routing Engine",
            event_type="routing_unassigned",
            payload={"reason": routing_reason},
            created_at=now,
        ))

    # Auto-theme tagging
    apply_theme_tags(db, ticket)

    # Create initial timeline event
    initial_event = TimelineEvent(
        ticket_id=ticket.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        event_type="status_change",
        payload={"from": None, "to": "New", "note": "Ticket created"},
        created_at=now,
    )
    db.add(initial_event)

    if chosen_agent:
        assign_event = TimelineEvent(
            ticket_id=ticket.id,
            actor_id=None,
            actor_name="System Routing Engine",
            event_type="assignment",
            payload={
                "assigned_to": str(chosen_agent.id),
                "agent_name": chosen_agent.full_name,
                "reason": routing_reason,
            },
            created_at=now,
        )
        db.add(assign_event)

    db.commit()
    db.refresh(ticket)

    resp = TicketResponse.model_validate(ticket)
    resp.agency_name = agency.name
    resp.assignee_name = chosen_agent.full_name if chosen_agent else None
    if current_user.role == "requester":
        resp.routing_reason = None
        resp.product_bug_link = None
        requester_links = []
        for link in created_links:
            linked_ticket = db.get(Ticket, link.target_id)
            if linked_ticket and linked_ticket.agency_id == current_user.agency_id:
                requester_links.append(link)
        created_links = requester_links
    resp.links = [LinkResponse.model_validate(lnk) for lnk in created_links]
    return resp


@router.get("/{id}", response_model=TicketDetailResponse)
def get_ticket(
    ticket: Ticket = Depends(agency_ticket_guard),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketDetailResponse:
    now = datetime.now(timezone.utc)

    # Recompute SLA status dynamically and update DB
    if ticket.sla_due:
        new_sla_status = compute_sla_status(
            sla_due=ticket.sla_due,
            now=now,
            created_at=ticket.created_at,
        )
        if new_sla_status != ticket.sla_status:
            ticket.sla_status = new_sla_status
            db.commit()
            db.refresh(ticket)

    # Fetch last 20 timeline events
    timeline_events = db.scalars(
        select(TimelineEvent)
        .where(TimelineEvent.ticket_id == ticket.id)
        .order_by(desc(TimelineEvent.created_at))
        .limit(20)
    ).all()

    # Fetch all links (source or target)
    links = db.scalars(
        select(TicketLink).where(
            or_(
                TicketLink.source_id == ticket.id,
                TicketLink.target_id == ticket.id,
            )
        ).order_by(desc(TicketLink.score))
    ).all()

    # Fetch escalation if active
    escalation = db.scalar(
        select(Escalation).where(Escalation.ticket_id == ticket.id)
    )

    detail = TicketDetailResponse.model_validate(ticket)
    if ticket.agency:
        detail.agency_name = ticket.agency.name
    if ticket.assignee:
        detail.assignee_name = ticket.assignee.full_name
    if current_user.role == "requester":
        timeline_events = [e for e in timeline_events if _timeline_visible_to_requester(e)]
        visible_links = []
        for link in links:
            other_id = link.target_id if link.source_id == ticket.id else link.source_id
            other_ticket = db.get(Ticket, other_id)
            if other_ticket and other_ticket.agency_id == current_user.agency_id:
                visible_links.append(link)
        links = visible_links
        detail.routing_reason = None
        detail.product_bug_link = None
    detail.timeline = [_timeline_response(e, requester_view=current_user.role == "requester") for e in timeline_events]
    detail.links = [LinkResponse.model_validate(l) for l in links]
    if escalation and current_user.role != "requester":
        detail.escalation = EscalationResponse.model_validate(escalation)

    return detail


@router.patch("/{id}", response_model=TicketResponse)
def update_ticket(
    ticket_update: TicketUpdate,
    ticket: Ticket = Depends(agency_ticket_guard),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketResponse:
    # Requesters may correct the customer-facing description only; operational fields are staff-owned.
    if current_user.role == "requester":
        if ticket.status in ["Closed", "Resolved"]:
            raise HTTPException(status_code=400, detail="Cannot edit resolved or closed tickets")
        forbidden = [name for name in ("priority", "intent", "check_in_date", "lcd", "product_bug_link") if getattr(ticket_update, name) is not None]
        if forbidden:
            raise HTTPException(status_code=403, detail=f"Requester cannot modify operational fields: {', '.join(forbidden)}")
    elif current_user.role not in {"agent", "lead", "escalation_manager"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    sla_needs_recompute = False
    if ticket_update.title is not None:
        ticket.title = ticket_update.title
    if ticket_update.description is not None:
        ticket.description = ticket_update.description
    if ticket_update.priority is not None:
        ticket.priority = ticket_update.priority
        sla_needs_recompute = True
    if ticket_update.intent is not None:
        ticket.intent = ticket_update.intent
    if ticket_update.check_in_date is not None:
        ticket.check_in_date = ticket_update.check_in_date
        sla_needs_recompute = True
    if ticket_update.lcd is not None:
        ticket.lcd = ticket_update.lcd
        sla_needs_recompute = True
    if ticket_update.product_bug_link is not None:
        ticket.product_bug_link = ticket_update.product_bug_link

    now = datetime.now(timezone.utc)
    ticket.updated_at = now

    if sla_needs_recompute:
        ticket.sla_due = compute_sla_due(
            priority=ticket.priority,
            created_at=ticket.created_at,
            check_in_date=ticket.check_in_date,
            lcd=ticket.lcd,
        )
        ticket.sla_status = compute_sla_status(
            sla_due=ticket.sla_due,
            now=now,
            created_at=ticket.created_at,
        )

    apply_theme_tags(db, ticket)
    db.commit()
    db.refresh(ticket)
    response = TicketResponse.model_validate(ticket)
    if current_user.role == "requester":
        response.routing_reason = None
        response.product_bug_link = None
    return response


@router.post("/{id}/transition", response_model=TicketResponse)
def transition_ticket(
    req: TicketTransitionRequest,
    ticket: Ticket = Depends(agency_ticket_guard),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketResponse:
    # Requester cannot manually transition ticket status
    if current_user.role == "requester":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requesters are not permitted to change ticket status",
        )

    allowed_targets = VALID_TRANSITIONS.get(ticket.status, [])
    if req.status not in allowed_targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from {ticket.status} to {req.status}. Allowed: {allowed_targets}",
        )

    old_status = ticket.status
    ticket.status = req.status
    now = datetime.now(timezone.utc)
    ticket.updated_at = now

    # Release workload exactly once when a ticket first becomes terminal.
    # Resolved -> Closed must not decrement the same assignment twice.
    if old_status not in {"Resolved", "Closed"} and req.status in {"Resolved", "Closed"} and ticket.assignee_id:
        assignee = db.get(User, ticket.assignee_id)
        if assignee and assignee.current_load > 0:
            assignee.current_load -= 1

    event = TimelineEvent(
        ticket_id=ticket.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        event_type="status_change",
        payload={"from": old_status, "to": req.status, "note": req.note},
        created_at=now,
    )
    db.add(event)

    db.commit()
    db.refresh(ticket)
    return TicketResponse.model_validate(ticket)


@router.post("/{id}/assign", response_model=TicketResponse)
def assign_ticket(
    req: TicketAssignRequest,
    ticket: Ticket = Depends(agency_ticket_guard),
    current_user: User = Depends(require_role("agent", "lead", "escalation_manager")),
    db: Session = Depends(get_db),
) -> TicketResponse:
    target_agent = db.get(User, req.agent_id)
    if not target_agent or target_agent.role not in ["agent", "lead", "escalation_manager"]:
        raise HTTPException(status_code=404, detail="Target agent not found or invalid role")
    old_assignee_id = ticket.assignee_id
    if old_assignee_id == target_agent.id:
        return TicketResponse.model_validate(ticket)
    # Snapshot side-thread recipient identities before transfer; they must remain unchanged.
    from app.models.side_conversation import SideConversation
    side_threads = db.scalars(select(SideConversation).where(SideConversation.ticket_id == ticket.id)).all()
    recipient_snapshot = {str(c.id): sorted(r.email.lower() for r in c.recipients) for c in side_threads}
    ticket.assignee_id = target_agent.id
    is_active_ticket = ticket.status not in {"Resolved", "Closed"}
    if is_active_ticket:
        target_agent.current_load = (target_agent.current_load or 0) + 1
    if old_assignee_id and is_active_ticket:
        old_agent = db.get(User, old_assignee_id)
        if old_agent and old_agent.current_load > 0:
            old_agent.current_load -= 1
    now = datetime.now(timezone.utc); ticket.updated_at = now
    db.add(TimelineEvent(ticket_id=ticket.id, actor_id=current_user.id, actor_name=current_user.full_name,
        event_type="assignment", payload={"from_assignee_id":str(old_assignee_id) if old_assignee_id else None,
        "assigned_to":str(target_agent.id), "agent_name":target_agent.full_name, "assigned_by":current_user.full_name}, created_at=now))
    for convo in side_threads:
        after = sorted(r.email.lower() for r in convo.recipients)
        if recipient_snapshot.get(str(convo.id), []) == after:
            db.add(TimelineEvent(ticket_id=ticket.id, actor_id=current_user.id, actor_name=current_user.full_name,
                event_type="side_convo_recipients_preserved", payload={"conversation_id":str(convo.id),
                "subject":convo.subject, "recipients":after, "from_assignee_id":str(old_assignee_id) if old_assignee_id else None,
                "to_assignee_id":str(target_agent.id)}, created_at=now))
    db.commit(); db.refresh(ticket)
    return TicketResponse.model_validate(ticket)


@router.post("/{id}/unassign", response_model=TicketResponse)
def unassign_ticket(
    ticket: Ticket = Depends(agency_ticket_guard),
    current_user: User = Depends(require_role("agent", "lead", "escalation_manager")),
    db: Session = Depends(get_db),
) -> TicketResponse:
    old_assignee_id = ticket.assignee_id
    if old_assignee_id is None:
        return TicketResponse.model_validate(ticket)
    old_agent = db.get(User, old_assignee_id)
    if ticket.status not in {"Resolved", "Closed"} and old_agent and old_agent.current_load > 0:
        old_agent.current_load -= 1
    ticket.assignee_id = None
    ticket.routing_reason = "Manually unassigned; ticket returned to Triage queue."
    now = datetime.now(timezone.utc); ticket.updated_at = now
    db.add(TimelineEvent(ticket_id=ticket.id, actor_id=current_user.id, actor_name=current_user.full_name,
        event_type="unassignment", payload={"from_assignee_id":str(old_assignee_id), "note":"Returned to Triage queue"}, created_at=now))
    db.commit(); db.refresh(ticket)
    return TicketResponse.model_validate(ticket)


@router.get("/{id}/timeline", response_model=List[TimelineResponse])
def get_ticket_timeline(
    ticket: Ticket = Depends(agency_ticket_guard),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[TimelineResponse]:
    events = db.scalars(
        select(TimelineEvent)
        .where(TimelineEvent.ticket_id == ticket.id)
        .order_by(desc(TimelineEvent.created_at))
        .limit(50)
    ).all()
    requester_view = current_user.role == "requester"
    if requester_view:
        events = [e for e in events if _timeline_visible_to_requester(e)]
    return [_timeline_response(e, requester_view=requester_view) for e in events]


@router.get("/{id}/links", response_model=List[LinkResponse])
def get_ticket_links(
    ticket: Ticket = Depends(agency_ticket_guard),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[LinkResponse]:
    links = db.scalars(
        select(TicketLink).where(
            or_(
                TicketLink.source_id == ticket.id,
                TicketLink.target_id == ticket.id,
            )
        ).order_by(desc(TicketLink.score))
    ).all()

    results = []
    for l in links:
        resp = LinkResponse.model_validate(l)
        other_id = l.target_id if l.source_id == ticket.id else l.source_id
        other_ticket = db.get(Ticket, other_id)
        if other_ticket and current_user.role == "requester" and other_ticket.agency_id != current_user.agency_id:
            # Keep cross-agency linkage internal; never reveal another agency's ticket content.
            continue
        if other_ticket:
            other_resp = TicketResponse.model_validate(other_ticket)
            if other_ticket.agency:
                other_resp.agency_name = other_ticket.agency.name
            if other_ticket.assignee:
                other_resp.assignee_name = other_ticket.assignee.full_name
            resp.linked_ticket = other_resp
        results.append(resp)
    return results


@router.post("/{id}/escalate", response_model=TicketResponse)
def escalate_ticket(
    req: TicketEscalateRequest,
    ticket: Ticket = Depends(agency_ticket_guard),
    current_user: User = Depends(require_role("agent", "lead", "escalation_manager")),
    db: Session = Depends(get_db),
) -> TicketResponse:
    if ticket.status in {"Resolved", "Closed"}:
        raise HTTPException(status_code=400, detail="Resolved or closed tickets cannot be escalated")

    em = db.get(User, req.escalation_manager_id)
    if not em or em.role != "escalation_manager":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target user must be an escalation_manager",
        )

    # Check if existing active escalation
    existing_esc = db.scalar(select(Escalation).where(Escalation.ticket_id == ticket.id))
    now = datetime.now(timezone.utc)

    if existing_esc:
        existing_esc.escalated_to_id = em.id
        existing_esc.reason = req.reason
        existing_esc.escalated_at = now
        existing_esc.resolved_at = None
    else:
        new_esc = Escalation(
            ticket_id=ticket.id,
            escalated_by_id=current_user.id,
            escalated_to_id=em.id,
            reason=req.reason,
            escalated_at=now,
        )
        db.add(new_esc)

    old_assignee_id = ticket.assignee_id
    ticket.status = "Escalated"
    ticket.assignee_id = em.id
    if old_assignee_id != em.id:
        em.current_load = (em.current_load or 0) + 1
    if old_assignee_id and old_assignee_id != em.id:
        old_agent = db.get(User, old_assignee_id)
        if old_agent and old_agent.current_load > 0:
            old_agent.current_load -= 1

    ticket.routing_reason = f"Escalated to {em.full_name} by {current_user.full_name}: {req.reason}"
    ticket.updated_at = now

    event = TimelineEvent(
        ticket_id=ticket.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        event_type="escalation",
        payload={
            "escalated_to": str(em.id),
            "em_name": em.full_name,
            "reason": req.reason,
        },
        created_at=now,
    )
    db.add(event)

    db.commit()
    db.refresh(ticket)
    return TicketResponse.model_validate(ticket)




@router.get("/{id}/comments", response_model=List[TicketCommentResponse])
def list_ticket_comments(
    ticket: Ticket = Depends(agency_ticket_guard),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(TicketComment).where(TicketComment.ticket_id == ticket.id).order_by(TicketComment.created_at.asc())
    if current_user.role == "requester": query = query.where(TicketComment.visibility == "public")
    elif current_user.role not in {"agent", "lead", "escalation_manager"}: raise HTTPException(status_code=403, detail="Insufficient permissions")
    return [TicketCommentResponse.model_validate(c) for c in db.scalars(query).all()]


@router.post("/{id}/comments", response_model=TicketCommentResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_comment(
    req: TicketCommentCreate,
    ticket: Ticket = Depends(agency_ticket_guard),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "requester":
        if req.visibility != "public": raise HTTPException(status_code=403, detail="Requesters cannot create internal notes")
        if ticket.status in {"Resolved", "Closed"}: raise HTTPException(status_code=400, detail="Cannot comment on resolved or closed tickets")
    elif current_user.role not in {"agent", "lead", "escalation_manager"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    now = datetime.now(timezone.utc)
    comment = TicketComment(ticket_id=ticket.id, author_id=current_user.id, author_name=current_user.full_name,
        body=req.body.strip(), visibility=req.visibility, created_at=now)
    db.add(comment)
    db.add(TimelineEvent(ticket_id=ticket.id, actor_id=current_user.id, actor_name=current_user.full_name,
        event_type="ticket_comment", payload={"visibility":req.visibility, "preview":req.body.strip()[:120]}, created_at=now))
    ticket.updated_at = now
    db.flush()
    apply_theme_tags(db, ticket)
    db.commit(); db.refresh(comment)
    return TicketCommentResponse.model_validate(comment)
