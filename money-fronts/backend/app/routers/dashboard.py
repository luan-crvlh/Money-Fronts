import calendar
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.config import settings

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud
from typing import Optional

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

from typing import Optional
# (Certifique-se de que Optional está importado no topo do seu arquivo)

from typing import Optional
# Certifique-se de que Optional e os outros imports já estão no topo do arquivo

@router.get("/summary")
def get_summary(
    month: int, 
    year: int, 
    account_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # 1. Gera recorrências automáticas
    today = date.today()
    if year == today.year and month == today.month:
        try:
            crud.generate_recurring_transactions(db, month, year)
        except Exception as e:
            print(f"Aviso: Erro ao gerar transações recorrentes automáticas: {e}")

    # 2. Filtros Base do Mês
    base_filters = [
        extract("month", models.Transaction.occurred_on) == month,
        extract("year", models.Transaction.occurred_on) == year,
    ]
    if account_id and account_id != "all":
        base_filters.append(models.Transaction.account_id == account_id)

    # 3. Calcula Receitas e Despesas do MÊS
    def total_for(tx_type: models.TransactionType) -> float:
        result = (
            db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
            .filter(models.Transaction.type == tx_type, *base_filters)
            .scalar()
        )
        return float(result or 0)

    total_income = total_for(models.TransactionType.INCOME)
    total_expense = total_for(models.TransactionType.EXPENSE)
    net_balance = total_income - total_expense

    # ==============================================================
    # NOVO: CÁLCULO DO SALDO GERAL (ATUAL) DA CONTA
    # ==============================================================
    # Pega o último dia do mês selecionado
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    # Busca todas as transações desde o início dos tempos até o fim do mês selecionado
    all_time_filters = [models.Transaction.occurred_on <= last_day]
    if account_id and account_id != "all":
        all_time_filters.append(models.Transaction.account_id == account_id)
        
    all_time_income = db.query(func.coalesce(func.sum(models.Transaction.amount), 0)).filter(
        models.Transaction.type == models.TransactionType.INCOME, *all_time_filters).scalar()
        
    all_time_expense = db.query(func.coalesce(func.sum(models.Transaction.amount), 0)).filter(
        models.Transaction.type == models.TransactionType.EXPENSE, *all_time_filters).scalar()

    # Busca as contas e tenta somar o 'initial_balance' (se esse campo existir no seu modelo)
    accounts_query = db.query(models.Account)
    if account_id and account_id != "all":
        accounts_query = accounts_query.filter(models.Account.id == account_id)
        
    total_initial_balance = sum(float(getattr(acc, 'initial_balance', 0.0) or 0.0) for acc in accounts_query.all())
    
    current_balance = total_initial_balance + float(all_time_income or 0) - float(all_time_expense or 0)
    # ==============================================================

    # 4. Livre para gastar por dia
    today = date.today()
    days_in_month = calendar.monthrange(year, month)[1]
    if today.year == year and today.month == month:
        days_remaining = max(days_in_month - today.day + 1, 1)
    else:
        days_remaining = days_in_month
    safe_to_spend_daily = round(net_balance / days_remaining, 2) if net_balance > 0 else 0.0

    # 5. Regra 50/30/20 (Com a busca unificada e ignorando maiúsculas/minúsculas)
    rule_breakdown = []
    rule_query = (
        db.query(
            models.Category.budget_group,
            func.coalesce(func.sum(models.Transaction.amount), 0).label("amount")
        )
        .join(models.Transaction, models.Transaction.category_id == models.Category.id)
        .filter(models.Transaction.type == models.TransactionType.EXPENSE, *base_filters)
        .group_by(models.Category.budget_group)
        .all()
    )

    spent_by_group = {}
    for row in rule_query:
        g_name = str(row.budget_group.value if hasattr(row.budget_group, 'value') else row.budget_group).lower()
        spent_by_group[g_name] = spent_by_group.get(g_name, 0.0) + float(row.amount)

    for group, planned_pct in settings.BUDGET_RULE.items():
        normalized_group = str(group.value if hasattr(group, 'value') else group).lower()
        spent = spent_by_group.get(normalized_group, 0.0)
        actual_pct = round((spent / total_income) * 100, 2) if total_income > 0 else 0.0
        
        # Como removemos o response_model, montamos o dicionário manualmente
        rule_breakdown.append({
            "group": group.value if hasattr(group, 'value') else group,
            "planned_percentage": planned_pct * 100,
            "actual_amount": spent,
            "actual_percentage": actual_pct,
        })

    # 6. Despesas por Categoria
    category_rows = (
        db.query(
            models.Transaction.category_id,
            models.Category.name,
            models.Category.color,
            func.coalesce(func.sum(models.Transaction.amount), 0),
        )
        .outerjoin(models.Category, models.Transaction.category_id == models.Category.id)
        .filter(models.Transaction.type == models.TransactionType.EXPENSE, *base_filters)
        .group_by(models.Transaction.category_id, models.Category.name, models.Category.color)
        .order_by(func.sum(models.Transaction.amount).desc())
        .all()
    )
    
    category_expenses = [
        {
            "category_id": row[0], 
            "category_name": row[1] or "Sem categoria",
            "color": row[2] or "#64748B", 
            "amount": float(row[3] or 0)
        }
        for row in category_rows
    ]

    # Retornamos o dicionário direto, adicionando o current_balance
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": net_balance,
        "current_balance": current_balance, # ENVIANDO O SALDO GERAL PARA O FRONTEND
        "safe_to_spend_daily": safe_to_spend_daily,
        "rule_50_30_20": rule_breakdown,
        "category_expenses": category_expenses,
    }