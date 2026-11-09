from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TicketExportFilter(BaseModel):
    status: Optional[str] = None
    intent: Optional[str] = None
    region: Optional[str] = None
    assignee_id: Optional[UUID] = None
    agency_id: Optional[UUID] = None
    tboh: Optional[str] = None
    unassigned: Optional[bool] = None
    escalated: Optional[bool] = None
