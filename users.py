"""
User administration (Admin only).

Creates accounts, updates roles, and removes users. No public registration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import User, UserRole
from app.schemas import UserCreate, UserListResponse, UserPublic, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])

admin_only = (UserRole.ADMIN,)


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users",
)
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*admin_only)),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> UserListResponse:
    rows, total = user_service.list_users(db, skip=skip, limit=limit)
    return UserListResponse(
        items=[UserPublic.model_validate(u) for u in rows],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*admin_only)),
) -> UserPublic:
    try:
        user = user_service.create_user(db, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "duplicate_email", "message": str(e)},
        ) from e
    return UserPublic.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserPublic,
    summary="Update user",
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*admin_only)),
) -> UserPublic:
    user = user_service.update_user(db, user_id, payload)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "User not found"},
        )
    return UserPublic.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*admin_only)),
) -> None:
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "cannot_delete_self", "message": "Cannot delete your own account"},
        )
    ok = user_service.delete_user(db, user_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "User not found"},
        )
