"""add is_on_duty to staff_members

Revision ID: 3d59847aad51
Revises: 05ef48b3d100
Create Date: 2026-07-02 16:21:41.928811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3d59847aad51'
down_revision: Union[str, Sequence[str], None] = '05ef48b3d100'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('staff_members', sa.Column('is_on_duty', sa.Boolean(), server_default=sa.text('true'), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('staff_members', 'is_on_duty')
