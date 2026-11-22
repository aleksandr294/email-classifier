"""add processing status

Revision ID: c3d4e5f6a7b8
Revises: b7c1d2e3f4a5
Create Date: 2026-11-21 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b7c1d2e3f4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block on older PostgreSQL versions
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE emailstatus ADD VALUE IF NOT EXISTS 'PROCESSING'")


def downgrade() -> None:
    # PostgreSQL cannot drop an enum value; move rows out of the state, the unused value stays in the type
    op.execute("UPDATE classification_record SET status = 'PENDING' WHERE status = 'PROCESSING'")
