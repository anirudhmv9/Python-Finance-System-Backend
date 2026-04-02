"""
Financial transaction CRUD and listing.

- **Viewer / Analyst**: read-only access to their own rows (GET).
- **Admin**: full CRUD; optional `user_id` query scopes listing to one user, or
  omit for all users' data.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import TransactionType, User, UserRole
from app.schemas import TransactionCreate, TransactionListResponse, TransactionPublic, TransactionUpdate
from app.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])

read_roles = (UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN)
admin_only = (UserRole.ADMIN,)


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="List transactions with filters",
)
def list_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*read_roles)),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    date_from: date | None = Query(None, description="Include rows on or after this date"),
    date_to: date | None = Query(None, description="Include rows on or before this date"),
    category: str | None = Query(None, max_length=128),
    transaction_type: TransactionType | None = Query(None, alias="type"),
    user_id: int | None = Query(
        None,
        description="Admin only: restrict to this owner's user id",
    ),
) -> TransactionListResponse:
    """
    Return a paginated list. Non-admins always see only their own data; the
    `user_id` parameter is ignored unless the caller is an admin.
    """
    scope_user_id = user_id if current_user.role == UserRole.ADMIN else None
    items, total = transaction_service.list_transactions(
        db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
        scope_user_id=scope_user_id,
    )
    return TransactionListResponse(
        items=[TransactionPublic.model_validate(x) for x in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionPublic,
    summary="Get one transaction",
)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*read_roles)),
) -> TransactionPublic:
    row = transaction_service.get_transaction(db, transaction_id, current_user)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Transaction not found"},
        )
    return TransactionPublic.model_validate(row)


@router.post(
    "",
    response_model=TransactionPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a transaction (Admin)",
)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*admin_only)),
) -> TransactionPublic:
    try:
        row = transaction_service.create_transaction(db, payload, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_target_user", "message": str(e)},
        ) from e
    return TransactionPublic.model_validate(row)


@router.patch(
    "/{transaction_id}",
    response_model=TransactionPublic,
    summary="Update a transaction (Admin)",
)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*admin_only)),
) -> TransactionPublic:
    row = transaction_service.update_transaction(db, transaction_id, payload, current_user)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Transaction not found"},
        )
    return TransactionPublic.model_validate(row)


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a transaction (Admin)",
)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*admin_only)),
) -> None:
    ok = transaction_service.delete_transaction(db, transaction_id, current_user)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Transaction not found"},
        )
