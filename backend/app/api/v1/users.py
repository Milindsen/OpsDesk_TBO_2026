from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = Query(None),
    current_user: User = Depends(require_role("agent", "lead", "escalation_manager")),
    db: Session = Depends(get_db),
) -> List[UserResponse]:
    """List staff identities for assignment and escalation pickers.

    Requester accounts are intentionally excluded: they do not need staff
    directory information to create or follow their own agency tickets.
    """
    allowed_roles = {"agent", "lead", "escalation_manager"}
    if role is not None and role not in allowed_roles:
        raise HTTPException(status_code=422, detail="Unsupported user role filter")
    query = select(User).where(User.role.in_(allowed_roles))
    if role:
        query = query.where(User.role == role)
    users = db.scalars(query.order_by(User.full_name.asc())).all()
    return [UserResponse.model_validate(user) for user in users]
