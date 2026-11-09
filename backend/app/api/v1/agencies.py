from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.agency import Agency
from app.models.user import User

router = APIRouter(prefix="/agencies", tags=["agencies"])


class AgencyResponse(BaseModel):
    id: UUID
    name: str
    region: str

    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=List[AgencyResponse])
def list_agencies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AgencyResponse]:
    """Return all agencies. Requesters only see their own."""
    if current_user.role == "requester":
        if current_user.agency_id:
            agency = db.get(Agency, current_user.agency_id)
            return [AgencyResponse.model_validate(agency)] if agency else []
        return []
    agencies = db.query(Agency).order_by(Agency.name).all()
    return [AgencyResponse.model_validate(a) for a in agencies]
