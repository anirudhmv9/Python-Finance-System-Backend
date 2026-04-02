"""
Authentication: login returns a JWT for subsequent Bearer requests.

There is no public self-registration; admins create accounts via `/users`.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, Token
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=Token,
    summary="Obtain access token",
    responses={
        401: {"description": "Invalid email or password"},
    },
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    """
    Authenticate with email/password and receive a JWT.

    Use `Authorization: Bearer <token>` on other endpoints.
    """
    user = db.scalars(
        select(User).where(User.email == payload.email.lower().strip())
    ).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Incorrect email or password"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "inactive_user", "message": "Account is disabled"},
        )

    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)
