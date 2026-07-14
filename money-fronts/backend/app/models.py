"""
Modelos de dados (ERSW RF01, RF02, RF03, RF05 / DAS seção 5).

Regras de cascata: ao apagar uma Categoria, as Transações associadas seguem
o paradigma de deleção em cascata / nullify (RN2 do ERSW).
"""
import enum
import uuid
from datetime import datetime, date

from sqlalchemy import (
    String, Numeric, Date, DateTime, ForeignKey, Enum, Boolean, Integer, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class TransactionType(str, enum.Enum):
    INCOME = "income"        # Receita
    EXPENSE = "expense"      # Despesa
    TRANSFER = "transfer"    # Transferência entre contas


class BudgetGroup(str, enum.Enum):
    """Classificação para a Regra 50/30/20 (RF04)."""
    NEEDS = "needs"      # Necessidades (50%)
    WANTS = "wants"       # Desejos (30%)
    SAVINGS = "savings"   # Investimentos / amortização (20%)


class AccountType(str, enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    CASH = "cash"
    INVESTMENT = "investment"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    icon: Mapped[str] = mapped_column(String(40), default="tag")
    color: Mapped[str] = mapped_column(String(20), default="#6366F1")
    budget_group: Mapped[BudgetGroup] = mapped_column(
        Enum(BudgetGroup), default=BudgetGroup.NEEDS
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # categoria pré-semeada (RF02)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",   # deleção em cascata (RN2)
        passive_deletes=True,
    )
    budgets: Mapped[list["Budget"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Account(Base):
    """Conta financeira para registrar origem/destino de fluxos (RF01)."""
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    institution: Mapped[str | None] = mapped_column(String(100), nullable=True)
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType), default=AccountType.CHECKING, nullable=False
    )
    initial_balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )

    # RF05: agendamento/recorrência
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule_id: Mapped[str | None] = mapped_column(
        ForeignKey("recurring_rules.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    category: Mapped["Category | None"] = relationship(back_populates="transactions")
    account: Mapped["Account"] = relationship(back_populates="transactions")
    recurrence_rule: Mapped["RecurringRule | None"] = relationship(back_populates="generated_transactions")


class RecurringRule(Base):
    """Regra de recorrência para despesas/receitas fixas (RF05)."""
    __tablename__ = "recurring_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    day_of_month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-28 recomendado
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    generated_transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="recurrence_rule"
    )


class Budget(Base):
    """Orçamento mensal por categoria (RF03 - envelope budgeting)."""
    __tablename__ = "budgets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    category_id: Mapped[str] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    limit_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    category: Mapped["Category"] = relationship(back_populates="budgets")
