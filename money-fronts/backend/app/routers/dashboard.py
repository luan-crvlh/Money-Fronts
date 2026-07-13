import calendar
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.config import settings

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=schemas.DashboardSummary)
def get_summary(month: int, year: int, db: Session = Depends(get_db)):
    def total_for(tx_type: models.TransactionType) -> float:
        result = (
            db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
            .filter(
                models.Transaction.type == tx_type,
                extract("month", models.Transaction.occurred_on) == month,
                extract("year", models.Transaction.occurred_on) == year,
            )
            .scalar()
        )
        return float(result or 0)

    total_income = total_for(models.TransactionType.INCOME)
    total_expense = total_for(models.TransactionType.EXPENSE)
    net_balance = total_income - total_expense

    # Safe-to-spend diário: saldo líquido remanescente / dias restantes no mês (RF04)
    today = date.today()
    days_in_month = calendar.monthrange(year, month)[1]
    if today.year == year and today.month == month:
        days_remaining = max(days_in_month - today.day + 1, 1)
    else:
        days_remaining = days_in_month
    safe_to_spend_daily = round(net_balance / days_remaining, 2) if net_balance > 0 else 0.0

    # Regra 50/30/20: agrupa gastos reais por budget_group da categoria
    rule_breakdown = []
    for group, planned_pct in settings.BUDGET_RULE.items():
        spent = (
            db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
            .join(models.Category, models.Transaction.category_id == models.Category.id)
            .filter(
                models.Category.budget_group == group,
                models.Transaction.type == models.TransactionType.EXPENSE,
                extract("month", models.Transaction.occurred_on) == month,
                extract("year", models.Transaction.occurred_on) == year,
            )
            .scalar()
        )
        spent = float(spent or 0)
        actual_pct = round((spent / total_income) * 100, 2) if total_income > 0 else 0.0
        rule_breakdown.append(
            schemas.RuleBreakdown(
                group=group,
                planned_percentage=planned_pct * 100,
                actual_amount=spent,
                actual_percentage=actual_pct,
            )
        )

    return schemas.DashboardSummary(
        total_income=total_income,
        total_expense=total_expense,
        net_balance=net_balance,
        safe_to_spend_daily=safe_to_spend_daily,
        rule_50_30_20=rule_breakdown,
    )
