"""
Pré-inicialização de categorias ubíquas no primeiro arranque (RF02 do ERSW).
"""
from sqlalchemy.orm import Session

from app.models import Category, BudgetGroup

DEFAULT_CATEGORIES = [
    # (nome, icone, cor, grupo 50/30/20)
    ("Alimentação", "utensils", "#F59E0B", BudgetGroup.NEEDS),
    ("Moradia", "home", "#10B981", BudgetGroup.NEEDS),
    ("Saúde", "heart-pulse", "#EF4444", BudgetGroup.NEEDS),
    ("Transporte", "car", "#3B82F6", BudgetGroup.NEEDS),
    ("Educação", "book", "#8B5CF6", BudgetGroup.NEEDS),
    ("Lazer", "party-popper", "#EC4899", BudgetGroup.WANTS),
    ("Compras", "shopping-bag", "#F97316", BudgetGroup.WANTS),
    ("Assinaturas", "repeat", "#06B6D4", BudgetGroup.WANTS),
    ("Investimentos", "trending-up", "#22C55E", BudgetGroup.SAVINGS),
    ("Dívidas", "credit-card", "#64748B", BudgetGroup.SAVINGS),
    ("Outros", "ellipsis", "#94A3B8", BudgetGroup.NEEDS),
]


def seed_default_categories(db: Session) -> None:
    existing = db.query(Category).count()
    if existing > 0:
        return  # já inicializado, não duplicar

    for name, icon, color, group in DEFAULT_CATEGORIES:
        db.add(Category(name=name, icon=icon, color=color, budget_group=group, is_system=True))
    db.commit()
