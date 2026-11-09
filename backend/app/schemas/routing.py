from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class CandidateScore(BaseModel):
    agent_id: str
    name: str
    score: int
    breakdown: Dict[str, Any]


class AutoRouteResponse(BaseModel):
    ticket_id: UUID
    chosen_agent_id: Optional[UUID] = None
    chosen_agent_name: Optional[str] = None
    scores: List[CandidateScore]
    reason: str
