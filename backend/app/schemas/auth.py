from datetime import datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    region: Optional[str] = None
    agency_id: Optional[UUID] = None
    shift_start: Optional[time] = None
    shift_end: Optional[time] = None
    availability: bool = True
    current_load: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: str
    user_id: str
    role: str
    agency_id: Optional[str] = None
