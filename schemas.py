"""
Pydantic models for request/response validation and OpenAPI documentation.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import TransactionType, UserRole


# --- Auth ---


class Token(BaseModel):
    

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    

    sub: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


# --- User ---


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Partial update for admin user management."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserPublic(BaseModel):
    

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserListResponse(BaseModel):
    

    items: list[UserPublic]
    total: int
    skip: int
    limit: int


# --- Transactions ---


class TransactionBase(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2, max_digits=14)
    type: TransactionType
    category: str = Field(min_length=1, max_length=128)
    occurred_on: date
    notes: str | None = Field(default=None, max_length=4000)


class TransactionCreate(TransactionBase):
    

    for_user_id: int | None = None


class TransactionUpdate(BaseModel):
    """All fields optional for PATCH-style updates."""

    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2, max_digits=14)
    type: TransactionType | None = None
    category: str | None = Field(default=None, min_length=1, max_length=128)
    occurred_on: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class TransactionPublic(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    """Paginated list of transactions."""

    items: list[TransactionPublic]
    total: int
    skip: int
    limit: int


# --- Summaries (responses produced by summary service) ---


class SummaryOverview(BaseModel):
   

    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal
    transaction_count: int
    date_from: date | None = None
    date_to: date | None = None


class CategoryBreakdownRow(BaseModel):
    category: str
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal


class MonthlyTotalRow(BaseModel):
    year_month: str  # "YYYY-MM"
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal


class RecentActivityItem(BaseModel):
    id: int
    amount: Decimal
    type: TransactionType
    category: str
    occurred_on: date
    notes: str | None


class SummaryAnalytics(BaseModel):
    

    overview: SummaryOverview
    category_breakdown: list[CategoryBreakdownRow]
    monthly_totals: list[MonthlyTotalRow]
    recent_activity: list[RecentActivityItem]
