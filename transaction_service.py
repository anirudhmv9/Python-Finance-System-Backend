"""
Transaction CRUD and listing with role-aware scoping.

- Viewer / Analyst: only rows where `user_id` matches their account.
- Admin: may list or mutate any user's rows; optional `scope_user_id` filters
  listing and summary queries to one user when provided.
"""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Transaction, TransactionType, User, UserRole
from app.schemas import TransactionCreate, TransactionUpdate


def _base_transaction_filter(
    query: Select,
    *,
    current_user: User,
    scope_user_id: int | None,
) -> Select:
    """
    Restrict rows to the current user unless admin is browsing a specific user
    or the entire system (scope_user_id None for admin = all users).
    """
    if current_user.role == UserRole.ADMIN:
        if scope_user_id is not None:
            return query.where(Transaction.user_id == scope_user_id)
        return query
    return query.where(Transaction.user_id == current_user.id)


def _apply_list_filters(
    query: Select,
    *,
    date_from,
    date_to,
    category: str | None,
    transaction_type: TransactionType | None,
) -> Select:
    if date_from is not None:
        query = query.where(Transaction.occurred_on >= date_from)
    if date_to is not None:
        query = query.where(Transaction.occurred_on <= date_to)
    if category is not None:
        query = query.where(Transaction.category == category)
    if transaction_type is not None:
        query = query.where(Transaction.type == transaction_type)
    return query


def _filtered_transaction_select(
    *,
    current_user: User,
    scope_user_id: int | None,
    date_from,
    date_to,
    category: str | None,
    transaction_type: TransactionType | None,
) -> Select:
    """
    SELECT over Transaction with role scope and list filters (no ordering).

    Shared by list endpoints and the summary service for consistent numbers.
    """
    q = select(Transaction)
    q = _base_transaction_filter(q, current_user=current_user, scope_user_id=scope_user_id)
    q = _apply_list_filters(
        q,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    return q


def list_transactions(
    db: Session,
    *,
    current_user: User,
    skip: int,
    limit: int,
    date_from,
    date_to,
    category: str | None,
    transaction_type: TransactionType | None,
    scope_user_id: int | None,
) -> tuple[list[Transaction], int]:
    """
    Return a page of transactions and total count for the same filter set.

    `scope_user_id` is honored only for admins; ignored for non-admins.
    """
    filtered = _filtered_transaction_select(
        current_user=current_user,
        scope_user_id=scope_user_id,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    count_sub = filtered.subquery()
    total = db.scalar(select(func.count()).select_from(count_sub)) or 0

    page_q = filtered.order_by(
        Transaction.occurred_on.desc(),
        Transaction.id.desc(),
    ).offset(skip).limit(limit)
    items = list(db.scalars(page_q).all())
    return items, total


def get_transaction(
    db: Session,
    transaction_id: int,
    current_user: User,
) -> Transaction | None:
    """Fetch one transaction if the user is allowed to see it."""
    q = select(Transaction).where(Transaction.id == transaction_id)
    if current_user.role != UserRole.ADMIN:
        q = q.where(Transaction.user_id == current_user.id)
    return db.scalars(q).first()


def create_transaction(
    db: Session,
    data: TransactionCreate,
    current_user: User,
) -> Transaction:
    """
    Create a transaction. Admin may set `for_user_id` to book on behalf of
    another user; others always book on themselves.
    """
    if current_user.role == UserRole.ADMIN and data.for_user_id is not None:
        target_user_id = data.for_user_id
        owner = db.get(User, target_user_id)
        if owner is None:
            raise ValueError("for_user_id does not exist")
    else:
        target_user_id = current_user.id

    row = Transaction(
        user_id=target_user_id,
        amount=data.amount,
        type=data.type,
        category=data.category.strip(),
        occurred_on=data.occurred_on,
        notes=data.notes.strip() if data.notes else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_transaction(
    db: Session,
    transaction_id: int,
    data: TransactionUpdate,
    current_user: User,
) -> Transaction | None:
    """Apply partial update. Admin can update any row; others only their own."""
    row = db.get(Transaction, transaction_id)
    if row is None:
        return None
    if current_user.role != UserRole.ADMIN and row.user_id != current_user.id:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "category" and isinstance(value, str):
            value = value.strip()
        if field == "notes" and value is not None:
            value = value.strip()
        setattr(row, field, value)

    db.commit()
    db.refresh(row)
    return row


def delete_transaction(
    db: Session,
    transaction_id: int,
    current_user: User,
) -> bool:
    """Delete by id if permitted. Returns True if a row was removed."""
    row = db.get(Transaction, transaction_id)
    if row is None:
        return False
    if current_user.role != UserRole.ADMIN and row.user_id != current_user.id:
        return False
    db.delete(row)
    db.commit()
    return True


