from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SideRecipientCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    name: Optional[str] = Field(default=None, max_length=255)


class SideRecipientResponse(BaseModel):
    id: UUID
    side_conversation_id: UUID
    email: str
    name: Optional[str] = None
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SideMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)
    kind: Literal["external", "internal"] = "external"


class SideMessageResponse(BaseModel):
    id: UUID
    side_conversation_id: UUID
    author_id: Optional[UUID] = None
    author_name: str
    body: str
    kind: str
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SideConversationCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=255)
    kind: Literal["supplier", "agency"] = "supplier"
    recipients: List[SideRecipientCreate] = Field(min_length=1, max_length=20)
    initial_message: Optional[str] = Field(default=None, max_length=10000)


class SideConversationResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    subject: str
    kind: str
    created_by_id: UUID
    created_at: datetime
    recipients: List[SideRecipientResponse] = Field(default_factory=list)
    messages: List[SideMessageResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
