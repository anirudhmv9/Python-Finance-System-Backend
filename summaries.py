"""
Summary and analytics endpoints.

Overview totals are available to **Viewer**, **Analyst**, and **Admin**.
Detailed analytics (category breakdown, monthly rollups, recent activity) are
restricted to **Analyst** and **Admin** per the assignment.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import TransactionType, User, UserRole
from app.schemas import SummaryAnalytics, SummaryOverview
from app.services import summary_service

router = APIRouter(prefix="/summaries", tags=["Summaries"])

overview_roles = (UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN)
analytics_roles = (UserRole.ANALYST, UserRole.ADMIN)


@router.get(
    "/overview",
    response_model=SummaryOverview,
    summary="Totals and balance (all read roles)",
)
def summary_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*overview_roles)),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    category: str | None = Query(None, max_length=128),
    transaction_type: TransactionType | None = Query(None, alias="type"),
    user_id: int | None = Query(None, description="Admin only: scope to this user"),
) -> SummaryOverview:
    scope_user_id = user_id if current_user.role == UserRole.ADMIN else None
    return summary_service.get_overview(
        db,
        current_user=current_user,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
        scope_user_id=scope_user_id,
    )


@router.get(
    "/analytics",
    response_model=SummaryAnalytics,
    summary="Detailed insights (Analyst & Admin)",
)
def summary_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*analytics_roles)),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    category: str | None = Query(None, max_length=128),
    transaction_type: TransactionType | None = Query(None, alias="type"),
    user_id: int | None = Query(None, description="Admin only: scope to this user"),
    recent_limit: int = Query(10, ge=1, le=50),
) -> SummaryAnalytics:
    """
    Category breakdown, monthly totals, and recent activity plus overview.

    **Viewers** receive HTTP 403 — use `/summaries/overview` for basic totals.
    """
    scope_user_id = user_id if current_user.role == UserRole.ADMIN else None
    return summary_service.get_full_analytics(
        db,
        current_user=current_user,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
        scope_user_id=scope_user_id,
        recent_limit=recent_limit,
    )
