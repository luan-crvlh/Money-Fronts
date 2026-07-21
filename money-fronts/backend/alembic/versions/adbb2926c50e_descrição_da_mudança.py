"""descrição da mudança

Revision ID: adbb2926c50e
Revises: 0001_initial_schema
Create Date: 2026-07-21 14:05:10.383033

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'adbb2926c50e'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Envelopamos a alteração no modo Batch
    with op.batch_alter_table('accounts') as batch_op:
        batch_op.alter_column(
            'account_type',
            existing_type=sa.VARCHAR(length=20),
            type_=sa.Enum('CHECKING', 'SAVINGS', 'CREDIT', 'CASH', 'INVESTMENT', name='accounttype'),
            existing_nullable=False,
            existing_server_default=sa.text("'checking'")
        )

def downgrade():
    # Fazemos o mesmo para o downgrade
    with op.batch_alter_table('accounts') as batch_op:
        batch_op.alter_column(
            'account_type',
            existing_type=sa.Enum('CHECKING', 'SAVINGS', 'CREDIT', 'CASH', 'INVESTMENT', name='accounttype'),
            type_=sa.VARCHAR(length=20),
            existing_nullable=False,
            existing_server_default=sa.text("'checking'")
        )