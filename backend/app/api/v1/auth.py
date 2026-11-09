import time
from collections import defaultdict
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import authenticate_user, create_access_token

router = APIRouter(tags=["auth"])

# Simple in-memory sliding window rate limiter: max 10 requests per minute per IP
LOGIN_ATTEMPTS: Dict[str, List[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60.0  # seconds
RATE_LIMIT_MAX = 10


def check_rate_limit(client_ip: str) -> None:
    now = time.time()
    attempts = LOGIN_ATTEMPTS[client_ip]
    # Filter attempts within window
    LOGIN_ATTEMPTS[client_ip] = [t for t in attempts if now - t < RATE_LIMIT_WINDOW]
    if len(LOGIN_ATTEMPTS[client_ip]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )
    LOGIN_ATTEMPTS[client_ip].append(now)


@router.post("/auth/login", response_model=TokenResponse)
def login(
    request: Request,
    credentials: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token_data = {
        "sub": user.email,
        "user_id": str(user.id),
        "role": user.role,
        "agency_id": str(user.agency_id) if user.agency_id else None,
    }
    access_token = create_access_token(data=token_data)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
