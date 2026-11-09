from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class LinkResponse(BaseModel):
    id: UUID
    source_id: UUID
    target_id: UUID
    link_type: str
    reason: str
    score: float
    created_at: datetime
    linked_ticket: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class TimelineResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    actor_id: Optional[UUID] = None
    actor_name: str
    event_type: str
    payload: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EscalationResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    escalated_by_id: UUID
    escalated_to_id: UUID
    reason: str
    escalated_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=20000)
    agency_id: Optional[UUID] = None
    tboh: str = Field(min_length=1, max_length=100)
    priority: Literal["P1", "P2", "P3", "P4"] = "P3"
    intent: Optional[Literal["refund", "cancellation", "amendment", "voucher", "inventory_sync", "payment", "special_request", "supplier_issue", "other"]] = None
    region: Optional[str] = Field(default=None, max_length=64)
    check_in_date: Optional[date] = None
    lcd: Optional[date] = None
    product_bug_link: Optional[str] = Field(default=None, max_length=500)


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, min_length=1, max_length=20000)
    priority: Optional[Literal["P1", "P2", "P3", "P4"]] = None
    intent: Optional[Literal["refund", "cancellation", "amendment", "voucher", "inventory_sync", "payment", "special_request", "supplier_issue", "other"]] = None
    check_in_date: Optional[date] = None
    lcd: Optional[date] = None
    product_bug_link: Optional[str] = None


class TicketTransitionRequest(BaseModel):
    status: Literal["New", "Open", "Pending", "Escalated", "Resolved", "Closed"]
    note: Optional[str] = Field(default=None, max_length=1000)


class TicketAssignRequest(BaseModel):
    agent_id: UUID = Field(validation_alias=AliasChoices("agent_id", "assignee_id"))


class TicketEscalateRequest(BaseModel):
    escalation_manager_id: UUID
    reason: str = Field(min_length=3, max_length=1000)


class TicketResponse(BaseModel):
    id: UUID
    title: str
    description: str
    agency_id: UUID
    agency_name: Optional[str] = None
    assignee_name: Optional[str] = None
    tboh: str
    priority: str
    intent: str
    status: str
    assignee_id: Optional[UUID] = None
    region: str
    check_in_date: Optional[date] = None
    lcd: Optional[date] = None
    sla_due: Optional[datetime] = None
    sla_status: str
    routing_reason: Optional[str] = None
    contact_count: int = 1
    product_bug_link: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    links: Optional[List[LinkResponse]] = None
    themes: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("agency_name", mode="before")
    @classmethod
    def resolve_agency_name(cls, v: Any, info: Any) -> Optional[str]:
        if isinstance(v, str):
            return v
        return None

    @field_validator("assignee_name", mode="before")
    @classmethod
    def resolve_assignee_name(cls, v: Any, info: Any) -> Optional[str]:
        if isinstance(v, str):
            return v
        return None

    @field_validator("themes", mode="before")
    @classmethod
    def coerce_themes(cls, v: Any) -> List[str]:
        """Convert TicketTheme ORM objects to plain theme-name strings."""
        if v is None:
            return []
        result: List[str] = []
        for item in v:
            if isinstance(item, str):
                result.append(item)
            elif hasattr(item, "theme") and item.theme is not None:
                # TicketTheme join-table row → Theme.name
                result.append(item.theme.name)
            elif hasattr(item, "name"):
                result.append(item.name)
        return result

    @field_validator("links", mode="before")
    @classmethod
    def coerce_links(cls, v: Any) -> List[Any]:
        """Accept None gracefully; actual link objects are validated by LinkResponse."""
        if v is None:
            return []
        return list(v)


class TicketDetailResponse(TicketResponse):
    timeline: List[TimelineResponse] = Field(default_factory=list)
    links: List[LinkResponse] = Field(default_factory=list)
    escalation: Optional[EscalationResponse] = None


class TicketListResponse(BaseModel):
    items: List[TicketResponse]
    total: int
    page: int
    page_size: int
