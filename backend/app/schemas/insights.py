from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class ThemeSampleTicket(BaseModel):
    id: UUID
    title: str
    tboh: str
    priority: str
    status: str
    created_at: datetime
    agency_id: UUID
    agency_name: str


class ThemeInsightResponse(BaseModel):
    theme_name: str
    count: int
    sample_tickets: List[ThemeSampleTicket]


class IntentSuggestRequest(BaseModel):
    title: str
    description: str


class IntentScore(BaseModel):
    intent: str
    confidence: float
