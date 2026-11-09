from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class TicketCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)
    visibility: Literal["internal", "public"] = "internal"

class TicketCommentResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    author_id: Optional[UUID] = None
    author_name: str
    body: str
    visibility: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
