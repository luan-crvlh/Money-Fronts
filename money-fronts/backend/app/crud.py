"""
Funções de acesso a dados (CRUD) usadas pelos routers.
"""
from datetime import date
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app import models, schemas


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
