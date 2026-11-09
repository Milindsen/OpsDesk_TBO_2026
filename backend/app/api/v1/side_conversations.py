from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import agency_ticket_guard, require_role
from app.models.side_conversation import (
    SideConversation,
    SideMessage,
    SideRecipient,
)
from app.models.ticket import Ticket
from app.models.timeline import TimelineEvent
from app.models.user import User
from app.services.theme_tagger import apply_theme_tags
from app.schemas.side_conversation import (
    SideConversationCreate,
    SideConversationResponse,
    SideMessageCreate,
    SideMessageResponse,
)

router = APIRouter(tags=["side_conversations"])


@router.get(
    "/tickets/{id}/side-conversations",
    response_model=List[SideConversationResponse],
)
def get_side_conversations(
    ticket: Ticket = Depends(agency_ticket_guard),
    current_user: User = Depends(require_role("agent", "lead", "escalation_manager")),
    db: Session = Depends(get_db),
) -> List[SideConversationResponse]:
    convos = db.scalars(
        select(SideConversation)
        .where(SideConversation.ticket_id == ticket.id)
        .options(
            selectinload(SideConversation.recipients),
            selectinload(SideConversation.messages),
        )
        .order_by(SideConversation.created_at)
    ).all()
    return [SideConversationResponse.model_validate(c) for c in convos]


@router.post(
    "/tickets/{id}/side-conversations",
    response_model=SideConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_side_conversation(
    conv_in: SideConversationCreate,
    ticket: Ticket = Depends(agency_ticket_guard),
    current_user: User = Depends(require_role("agent", "lead", "escalation_manager")),
    db: Session = Depends(get_db),
) -> SideConversationResponse:
    now = datetime.now(timezone.utc)
    conv = SideConversation(
        ticket_id=ticket.id,
        subject=conv_in.subject,
        kind=conv_in.kind,
        created_by_id=current_user.id,
        created_at=now,
    )
    db.add(conv)
    db.flush()

    for r in conv_in.recipients:
        rec = SideRecipient(
            side_conversation_id=conv.id,
            email=r.email,
            name=r.name,
            added_at=now,
        )
        db.add(rec)

    if conv_in.initial_message:
        msg = SideMessage(
            side_conversation_id=conv.id,
            author_id=current_user.id,
            author_name=current_user.full_name,
            body=conv_in.initial_message,
            kind="external",
            sent_at=now,
        )
        db.add(msg)

    # Timeline event
    recipient_emails = [r.email for r in conv_in.recipients]
    event = TimelineEvent(
        ticket_id=ticket.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        event_type="side_convo",
        payload={
            "conversation_id": str(conv.id),
            "subject": conv.subject,
            "kind": conv.kind,
            "recipients": recipient_emails,
        },
        created_at=now,
    )
    db.add(event)
    ticket.updated_at = now
    db.flush()
    apply_theme_tags(db, ticket)

    db.commit()
    db.refresh(conv)

    # Reload with relationships
    conv_loaded = db.scalar(
        select(SideConversation)
        .where(SideConversation.id == conv.id)
        .options(
            selectinload(SideConversation.recipients),
            selectinload(SideConversation.messages),
        )
    )
    return SideConversationResponse.model_validate(conv_loaded)


@router.post(
    "/side-conversations/{id}/messages",
    response_model=SideMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_side_message(
    id: UUID,
    msg_in: SideMessageCreate,
    current_user: User = Depends(require_role("agent", "lead", "escalation_manager")),
    db: Session = Depends(get_db),
) -> SideMessageResponse:
    conv = db.get(SideConversation, id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Side conversation not found",
        )

    ticket = db.get(Ticket, conv.ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Parent ticket not found")

    if msg_in.kind not in {"internal", "external"}:
        raise HTTPException(status_code=422, detail="Message kind must be internal or external")
    now = datetime.now(timezone.utc)
    msg = SideMessage(
        side_conversation_id=conv.id,
        author_id=current_user.id,
        author_name=current_user.full_name,
        body=msg_in.body,
        kind=msg_in.kind,
        sent_at=now,
    )
    db.add(msg)

    event = TimelineEvent(
        ticket_id=conv.ticket_id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        event_type="side_convo",
        payload={
            "conversation_id": str(conv.id),
            "message_kind": msg.kind,
            "action": "new_message",
        },
        created_at=now,
    )
    db.add(event)
    ticket.updated_at = now
    db.flush()
    if msg.kind == "external":
        apply_theme_tags(db, ticket)

    db.commit()
    db.refresh(msg)
    return SideMessageResponse.model_validate(msg)
