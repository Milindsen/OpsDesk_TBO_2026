from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.escalation import Escalation
from app.models.user import User
from app.schemas.ticket import EscalationResponse

router = APIRouter(prefix="/escalations", tags=["escalations"])


@router.get("", response_model=List[EscalationResponse])
def list_escalations(
    current_user: User = Depends(require_role("agent", "lead", "escalation_manager")),
    db: Session = Depends(get_db),
) -> List[EscalationResponse]:
    query = select(Escalation).order_by(desc(Escalation.escalated_at))
    if current_user.role == "escalation_manager":
        query = query.where(Escalation.escalated_to_id == current_user.id)
    escalations = db.scalars(query).all()
    return [EscalationResponse.model_validate(e) for e in escalations]


@router.get("/{id}", response_model=EscalationResponse)
def get_escalation(
    id: UUID,
    current_user: User = Depends(require_role("agent", "lead", "escalation_manager")),
    db: Session = Depends(get_db),
) -> EscalationResponse:
    esc = db.get(Escalation, id)
    if not esc or (current_user.role == "escalation_manager" and esc.escalated_to_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Escalation not found",
        )
    return EscalationResponse.model_validate(esc)
