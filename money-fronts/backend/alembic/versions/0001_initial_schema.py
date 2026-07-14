"""Cria e atualiza o esquema local inicial do Money Fronts.

Revision ID: 0001_initial_schema
Revises:
"""
from alembic import op
import sqlalchemy as sa

from app.database import Base
from app import models  # noqa: F401 - registra os modelos no metadata


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Compatível tanto com instalações novas quanto com o scaffold anterior."""
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

    columns = {column["name"] for column in sa.inspect(bind).get_columns("accounts")}
    if "institution" not in columns:
        op.add_column("accounts", sa.Column("institution", sa.String(length=100), nullable=True))
    if "account_type" not in columns:
        op.add_column(
            "accounts",
            sa.Column("account_type", sa.String(length=20), nullable=False, server_default="checking"),
        )


def downgrade() -> None:
    # A primeira migração preserva os dados financeiros locais; reversão não é automática.
    pass
