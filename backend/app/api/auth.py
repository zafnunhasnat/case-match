
import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.doctor import Doctor
from app.services.rate_limit import limiter
from app.services.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    email = credentials.email.strip().lower()

    doctor = db.scalar(
        select(Doctor).where(Doctor.email == email)
    )

    # Use the same error for an unknown email and an incorrect password.
    if doctor is None or not verify_password(
        credentials.password,
        doctor.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(str(doctor.id))

    return TokenResponse(access_token=token)


def get_current_user(
    token: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Doctor:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        payload = decode_access_token(token.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Look up the user on every request so role changes take effect.
    doctor = db.scalar(
        select(Doctor).where(Doctor.id == user_id)
    )

    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return doctor


def require_reviewer(
    current_user: Doctor = Depends(get_current_user),
) -> Doctor:
    if current_user.role not in ("reviewer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer access required",
        )

    return current_user


def require_admin(
    current_user: Doctor = Depends(get_current_user),
) -> Doctor:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )

    return current_user


def log_audit_event(
    db: Session,
    username: str,
    action: str,
    details: str,
    ip_address: str,
):
    audit_sql = text("""
        INSERT INTO search_audit_logs
        (username, action, details, ip_address, timestamp)
        VALUES (:username, :action, :details, :ip_address, NOW())
    """)

    db.execute(
        audit_sql,
        {
            "username": username,
            "action": action,
            "details": details,
            "ip_address": ip_address,
        },
    )
    db.commit()
