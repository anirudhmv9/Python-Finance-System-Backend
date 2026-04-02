"""Admin-only user management: list, create, update, deactivate."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.security import get_password_hash


def list_users(db: Session, *, skip: int, limit: int) -> tuple[list[User], int]:
    """Paginated user directory ordered by id."""
    total = int(db.scalar(select(func.count(User.id))) or 0)
    q = select(User).order_by(User.id.asc()).offset(skip).limit(limit)
    return list(db.scalars(q).all()), int(total)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email)).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, data: UserCreate) -> User:
    """Create a new user; raises ValueError if email already exists."""
    if get_user_by_email(db, data.email) is not None:
        raise ValueError("Email already registered")
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name.strip(),
        role=data.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, data: UserUpdate) -> User | None:
    """Partial update. Returns None if user missing."""
    user = db.get(User, user_id)
    if user is None:
        return None
    payload = data.model_dump(exclude_unset=True)
    if "password" in payload and payload["password"] is not None:
        user.hashed_password = get_password_hash(payload.pop("password"))
    for key, value in payload.items():
        if key == "full_name" and isinstance(value, str):
            value = value.strip()
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    """
    Hard delete user and cascading transactions.

    Returns False if the user did not exist.
    """
    user = db.get(User, user_id)
    if user is None:
        return False
    db.delete(user)
    db.commit()
    return True
