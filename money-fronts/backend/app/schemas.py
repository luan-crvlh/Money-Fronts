"""
Schemas Pydantic (validação de tipos - RF01 justifica uso do FastAPI/Pydantic).
"""
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models import TransactionType, BudgetGroup, AccountType


# ---------- Category ----------
class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    icon: str = "tag"
    color: str = "#6366F1"
    budget_group: BudgetGroup = BudgetGroup.NEEDS


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    is_system: bool
    created_at: datetime


# ---------- Account ----------
class AccountBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    institution: str | None = Field(default=None, max_length=100)
    account_type: AccountType = AccountType.CHECKING
    initial_balance: float = 0


class AccountCreate(AccountBase):
    pass


class AccountOut(AccountBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Transaction ----------
class TransactionBase(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)
    type: TransactionType
    occurred_on: date
    notes: str | None = None
    category_id: str | None = None
    account_id: str


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    description: str | None = None
    amount: float | None = None
    type: TransactionType | None = None
    occurred_on: date | None = None
    notes: str | None = None
    category_id: str | None = None
    account_id: str | None = None


class TransactionOut(TransactionBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    is_recurring: bool
    created_at: datetime


# ---------- Budget ----------
class BudgetBase(BaseModel):
    category_id: str
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)
    limit_amount: float = Field(gt=0)


class BudgetCreate(BudgetBase):
    pass


class BudgetOut(BudgetBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


class BudgetProgress(BaseModel):
    category_id: str
    category_name: str
    limit_amount: float
    spent_amount: float
    percentage: float


# ---------- Recorrência ----------
class RecurringRuleBase(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)
    type: TransactionType
    category_id: str | None = None
    account_id: str
    day_of_month: int = Field(ge=1, le=28)
    active: bool = True


class RecurringRuleCreate(RecurringRuleBase):
    pass


class RecurringRuleOut(RecurringRuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


class CategoryExpense(BaseModel):
    category_id: str | None
    category_name: str
    color: str
    amount: float


# ---------- Dashboard / 50-30-20 ----------
class RuleBreakdown(BaseModel):
    group: BudgetGroup
    planned_percentage: float
    actual_amount: float
    actual_percentage: float


class DashboardSummary(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float
    safe_to_spend_daily: float
    rule_50_30_20: list[RuleBreakdown]
    category_expenses: list[CategoryExpense]
