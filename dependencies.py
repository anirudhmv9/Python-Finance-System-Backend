

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.security import decode_token

# Bearer token in Authorization header
security = HTTPBearer(auto_error=True)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail={
        "code": "auth_required",
        "message": "Could not validate credentials",
    },
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Parse Bearer JWT and load the active user."""
    token = credentials.credentials
    sub = decode_token(token)
    if sub is None:
        raise credentials_exception
    try:
        user_id = int(sub)
    except ValueError:
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_roles(*roles: UserRole):
    """
    Factory returning a dependency that enforces one of the allowed roles.

    Example:
        @router.get("/admin-only", dependencies=[Depends(require_roles(UserRole.ADMIN))])
    """

    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "forbidden",
                    "message": "Insufficient permissions for this resource",
                    "required_roles": [r.value for r in roles],
                },
            )
        return user

    return _dep
