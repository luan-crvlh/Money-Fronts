"""
Funções de acesso a dados (CRUD) usadas pelos routers.
"""
from datetime import date
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app import models, schemas

from typing import Optional
from sqlalchemy.orm import Session
from app.models import Transaction, TransactionType, Category, Account
import calendar

def get_dashboard_metrics(db: Session, month: int, year: int, account_id: Optional[str] = None):
    """
    Retorna as métricas consolidadas para o Dashboard, incluindo Regra 50/30/20 e Saldo Diário.
    Blindado contra divisões por zero (ex: quando há despesas mas não há receitas).
    """
    # 1. Filtros Base
    date_filters = [
        extract('month', Transaction.occurred_on) == month,
        extract('year', Transaction.occurred_on) == year
    ]

    if account_id and account_id != "all":
        date_filters.append(Transaction.account_id == account_id)

    # 2. Totalizadores (Seguros contra nulos)
    total_income = db.query(func.sum(Transaction.amount)).filter(
        *date_filters, Transaction.type == TransactionType.INCOME
    ).scalar() or 0.0

    total_expense = db.query(func.sum(Transaction.amount)).filter(
        *date_filters, Transaction.type == TransactionType.EXPENSE
    ).scalar() or 0.0

    net_balance = total_income - total_expense

    # 3. Despesas por Categoria (Gráfico)
    expenses_by_category_query = (
        db.query(
            Category.name.label("category_name"), 
            Category.color, 
            func.sum(Transaction.amount).label("amount")
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(*date_filters, Transaction.type == TransactionType.EXPENSE)
        .group_by(Category.id)
        .all()
    )

    category_expenses = [
        {
            "category_name": row.category_name, 
            "color": row.color, 
            "amount": float(row.amount)
        }
        for row in expenses_by_category_query
    ]

    # 4. Cálculo Seguro da Regra 50/30/20
    rule_query = (
        db.query(
            Category.budget_group,
            func.sum(Transaction.amount).label("amount")
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(*date_filters, Transaction.type == TransactionType.EXPENSE)
        .group_by(Category.budget_group)
        .all()
    )

    # Dicionário auxiliar para mapear gastos
    grouped_expenses = {}
    for row in rule_query:
        # Extrai a string do enum com segurança
        group_name = str(row.budget_group.value if hasattr(row.budget_group, 'value') else row.budget_group).lower()
        grouped_expenses[group_name] = float(row.amount)

    planned_rules = {"needs": 50.0, "wants": 30.0, "savings": 20.0}
    rule_50_30_20 = []

    for group, planned_pct in planned_rules.items():
        spent = grouped_expenses.get(group, 0.0)
        
        # A TRAVA DE SEGURANÇA: Só divide se houver receita
        if total_income > 0:
            actual_pct = (spent / total_income) * 100
        else:
            actual_pct = 0.0

        rule_50_30_20.append({
            "group": group,
            "actual_percentage": actual_pct,
            "planned_percentage": planned_pct
        })

    # 5. Cálculo do Livre para Gastar / Dia
    _, days_in_month = calendar.monthrange(year, month)
    
    today = date.today()
    if today.year == year and today.month == month:
        # Se for o mês atual, pega os dias restantes do mês
        days_left = days_in_month - today.day + 1
    else:
        # Se for outro mês, usa o mês inteiro
        days_left = days_in_month
        
    # Se o saldo for negativo, o livre para gastar é zero
    safe_to_spend_daily = (net_balance / days_left) if net_balance > 0 and days_left > 0 else 0.0

    # 6. Retorno padronizado com o que a interface original espera
    return {
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "net_balance": float(net_balance),             # Compatível com interface nativa
        "monthly_balance": float(net_balance),         # Fallback
        "safe_to_spend_daily": float(safe_to_spend_daily),
        "rule_50_30_20": rule_50_30_20,
        "category_expenses": category_expenses,        # Compatível com interface nativa
        "expenses_by_category": category_expenses      # Fallback
    }
# ---------- Categories ----------
def list_categories(db: Session) -> list[models.Category]:
    return db.query(models.Category).order_by(models.Category.name).all()


def create_category(db: Session, data: schemas.CategoryCreate) -> models.Category:
    obj = models.Category(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_category(db: Session, category_id: str) -> bool:
    obj = db.get(models.Category, category_id)
    if not obj:
        return False
    db.delete(obj)  # cascade cuida das transações associadas (RN2)
    db.commit()
    return True


# ---------- Accounts ----------
def list_accounts(db: Session) -> list[models.Account]:
    return db.query(models.Account).order_by(models.Account.name).all()


def create_account(db: Session, data: schemas.AccountCreate) -> models.Account:
    obj = models.Account(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_account(db: Session, account_id: str) -> bool:
    obj = db.get(models.Account, account_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# ---------- Transactions ----------
def list_transactions(
    db: Session,
    month: int | None = None,
    year: int | None = None,
    category_id: str | None = None,
    account_id: str | None = None,
) -> list[models.Transaction]:
    q = db.query(models.Transaction)
    if month:
        q = q.filter(extract("month", models.Transaction.occurred_on) == month)
    if year:
        q = q.filter(extract("year", models.Transaction.occurred_on) == year)
    if category_id:
        q = q.filter(models.Transaction.category_id == category_id)
    if account_id:
        q = q.filter(models.Transaction.account_id == account_id)
    return q.order_by(models.Transaction.occurred_on.desc()).all()


def create_transaction(db: Session, data: schemas.TransactionCreate) -> models.Transaction:
    obj = models.Transaction(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_transaction(
    db: Session, transaction_id: str, data: schemas.TransactionUpdate
) -> models.Transaction | None:
    obj = db.get(models.Transaction, transaction_id)
    if not obj:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_transaction(db: Session, transaction_id: str) -> bool:
    obj = db.get(models.Transaction, transaction_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# ---------- Recurring rules ----------
def list_recurring_rules(db: Session) -> list[models.RecurringRule]:
    return db.query(models.RecurringRule).order_by(models.RecurringRule.description).all()


def create_recurring_rule(db: Session, data: schemas.RecurringRuleCreate) -> models.RecurringRule:
    obj = models.RecurringRule(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_recurring_rule(db: Session, rule_id: str) -> bool:
    obj = db.get(models.RecurringRule, rule_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# Certifique-se de que o calendário está importado no topo do arquivo: import calendar

def generate_recurring_transactions(db: Session, month: int, year: int) -> int:
    """Cria somente os lançamentos ainda ausentes para cada regra ativa no mês (Blindado contra meses curtos)."""
    created = 0
    
    # Pega o último dia válido do mês selecionado (ex: 28 para Fevereiro, 30 para Abril)
    _, max_days_in_month = calendar.monthrange(year, month)
    
    for rule in db.query(models.RecurringRule).filter(models.RecurringRule.active.is_(True)).all():
        
        # A BLINDAGEM: Se o dia da cobrança for 31 e o mês for Fevereiro, cobra no dia 28.
        safe_day = min(rule.day_of_month, max_days_in_month)
        
        occurred_on = date(year, month, safe_day)
        
        exists = (
            db.query(models.Transaction.id)
            .filter(
                models.Transaction.recurrence_rule_id == rule.id,
                models.Transaction.occurred_on == occurred_on,
            )
            .first()
        )
        
        if not exists:
            db.add(models.Transaction(
                description=rule.description,
                amount=rule.amount,
                type=rule.type,
                occurred_on=occurred_on,
                category_id=rule.category_id,
                account_id=rule.account_id,
                is_recurring=True,
                recurrence_rule_id=rule.id,
            ))
            created += 1
            
    if created:
        db.commit()
    return created


# ---------- Budgets ----------
def list_budgets(db: Session, month: int, year: int) -> list[models.Budget]:
    return (
        db.query(models.Budget)
        .filter(models.Budget.month == month, models.Budget.year == year)
        .all()
    )


def create_budget(db: Session, data: schemas.BudgetCreate) -> models.Budget:
    obj = models.Budget(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def budget_progress(db: Session, month: int, year: int) -> list[schemas.BudgetProgress]:
    budgets = list_budgets(db, month, year)
    results = []
    for b in budgets:
        spent = (
            db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
            .filter(
                models.Transaction.category_id == b.category_id,
                models.Transaction.type == models.TransactionType.EXPENSE,
                extract("month", models.Transaction.occurred_on) == month,
                extract("year", models.Transaction.occurred_on) == year,
            )
            .scalar()
        )
        spent = float(spent or 0)
        limit = float(b.limit_amount)
        results.append(
            schemas.BudgetProgress(
                category_id=b.category_id,
                category_name=b.category.name,
                limit_amount=limit,
                spent_amount=spent,
                percentage=round((spent / limit) * 100, 2) if limit > 0 else 0,
            )
        )
    return results
