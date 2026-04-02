"""
Financial summary and analytics logic (service layer only).

All aggregates used by dashboards and reports are computed here — not in route
handlers — so rules stay testable and consistent with list filters.

Uses the same filter pipeline as `transaction_service.list_transactions` via
`_filtered_transaction_select` so totals always match the visible list.
"""

from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import Transaction, TransactionType, User
from app.schemas import (
    CategoryBreakdownRow,
    MonthlyTotalRow,
    RecentActivityItem,
    SummaryAnalytics,
    SummaryOverview,
)
from app.services.transaction_service import _filtered_transaction_select


def _decimal(val) -> Decimal:
    """Normalize DB numeric to Decimal for JSON responses."""
    if val is None:
        return Decimal("0")
    return Decimal(str(val))


def get_overview(
    db: Session,
    *,
    current_user: User,
    date_from,
    date_to,
    category: str | None,
    transaction_type: TransactionType | None,
    scope_user_id: int | None,
) -> SummaryOverview:
    """
    Totals and balance for the current filter set.

    Available to Viewer, Analyst, and Admin (see router dependencies).
    """
    filtered = _filtered_transaction_select(
        current_user=current_user,
        scope_user_id=scope_user_id,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    subq = filtered.subquery()
    t = subq.c

    income_expr = func.coalesce(
        func.sum(case((t.type == TransactionType.INCOME, t.amount), else_=0)),
        0,
    )
    expense_expr = func.coalesce(
        func.sum(case((t.type == TransactionType.EXPENSE, t.amount), else_=0)),
        0,
    )
    count_expr = func.count(t.id)

    row = db.execute(select(income_expr, expense_expr, count_expr).select_from(subq)).one()

    total_income = _decimal(row[0])
    total_expenses = _decimal(row[1])
    return SummaryOverview(
        total_income=total_income,
        total_expenses=total_expenses,
        balance=total_income - total_expenses,
        transaction_count=int(row[2]),
        date_from=date_from,
        date_to=date_to,
    )


def get_category_breakdown(
    db: Session,
    *,
    current_user: User,
    date_from,
    date_to,
    category: str | None,
    transaction_type: TransactionType | None,
    scope_user_id: int | None,
) -> list[CategoryBreakdownRow]:
    """Per-category income, expenses, and net for the filtered set."""
    filtered = _filtered_transaction_select(
        current_user=current_user,
        scope_user_id=scope_user_id,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    subq = filtered.subquery()
    t = subq.c

    income_sum = func.coalesce(
        func.sum(case((t.type == TransactionType.INCOME, t.amount), else_=0)),
        0,
    )
    expense_sum = func.coalesce(
        func.sum(case((t.type == TransactionType.EXPENSE, t.amount), else_=0)),
        0,
    )

    stmt = (
        select(t.category, income_sum, expense_sum)
        .select_from(subq)
        .group_by(t.category)
        .order_by(t.category)
    )
    rows = db.execute(stmt).all()
    out: list[CategoryBreakdownRow] = []
    for cat, inc, exp in rows:
        inc_d, exp_d = _decimal(inc), _decimal(exp)
        out.append(
            CategoryBreakdownRow(
                category=cat,
                total_income=inc_d,
                total_expenses=exp_d,
                net=inc_d - exp_d,
            )
        )
    return out


def get_monthly_totals(
    db: Session,
    *,
    current_user: User,
    date_from,
    date_to,
    category: str | None,
    transaction_type: TransactionType | None,
    scope_user_id: int | None,
) -> list[MonthlyTotalRow]:
    """
    Roll up income and expenses by calendar month for SQLite.
    """
    filtered = _filtered_transaction_select(
        current_user=current_user,
        scope_user_id=scope_user_id,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    subq = filtered.subquery()
    t = subq.c

    ym = func.strftime("%Y-%m", t.occurred_on).label("year_month")
    income_sum = func.coalesce(
        func.sum(case((t.type == TransactionType.INCOME, t.amount), else_=0)),
        0,
    )
    expense_sum = func.coalesce(
        func.sum(case((t.type == TransactionType.EXPENSE, t.amount), else_=0)),
        0,
    )

    stmt = (
        select(ym, income_sum, expense_sum)
        .select_from(subq)
        .group_by(ym)
        .order_by(ym)
    )
    rows = db.execute(stmt).all()
    out: list[MonthlyTotalRow] = []
    for ym_s, inc, exp in rows:
        inc_d, exp_d = _decimal(inc), _decimal(exp)
        out.append(
            MonthlyTotalRow(
                year_month=str(ym_s),
                total_income=inc_d,
                total_expenses=exp_d,
                net=inc_d - exp_d,
            )
        )
    return out


def get_recent_activity(
    db: Session,
    *,
    current_user: User,
    date_from,
    date_to,
    category: str | None,
    transaction_type: TransactionType | None,
    scope_user_id: int | None,
    limit: int = 10,
) -> list[RecentActivityItem]:
    """Most recent lines by `occurred_on` (then id) within the filter window."""
    filtered = _filtered_transaction_select(
        current_user=current_user,
        scope_user_id=scope_user_id,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    q = filtered.order_by(Transaction.occurred_on.desc(), Transaction.id.desc()).limit(limit)
    rows = db.scalars(q).all()
    return [
        RecentActivityItem(
            id=r.id,
            amount=r.amount,
            type=r.type,
            category=r.category,
            occurred_on=r.occurred_on,
            notes=r.notes,
        )
        for r in rows
    ]


def get_full_analytics(
    db: Session,
    *,
    current_user: User,
    date_from,
    date_to,
    category: str | None,
    transaction_type: TransactionType | None,
    scope_user_id: int | None,
    recent_limit: int = 10,
) -> SummaryAnalytics:
    """
    Analyst / Admin bundle: overview plus breakdowns and recent activity.

    Composition only — each piece delegates to the helpers above.
    """
    overview = get_overview(
        db,
        current_user=current_user,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
        scope_user_id=scope_user_id,
    )
    return SummaryAnalytics(
        overview=overview,
        category_breakdown=get_category_breakdown(
            db,
            current_user=current_user,
            date_from=date_from,
            date_to=date_to,
            category=category,
            transaction_type=transaction_type,
            scope_user_id=scope_user_id,
        ),
        monthly_totals=get_monthly_totals(
            db,
            current_user=current_user,
            date_from=date_from,
            date_to=date_to,
            category=category,
            transaction_type=transaction_type,
            scope_user_id=scope_user_id,
        ),
        recent_activity=get_recent_activity(
            db,
            current_user=current_user,
            date_from=date_from,
            date_to=date_to,
            category=category,
            transaction_type=transaction_type,
            scope_user_id=scope_user_id,
            limit=recent_limit,
        ),
    )
