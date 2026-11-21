"""add injection_detected

Revision ID: b7c1d2e3f4a5
Revises: 88f3eec38130
Create Date: 2026-11-21 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7c1d2e3f4a5'
down_revision: Union[str, Sequence[str], None] = '88f3eec38130'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'classification_record',
        sa.Column('injection_detected', sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('classification_record', 'injection_detected')
