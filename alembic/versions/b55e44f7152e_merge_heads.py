"""merge heads

Revision ID: b55e44f7152e
Revises: 7dcec49dc4bb, 90f5d6fcecb1
Create Date: 2026-07-08 12:44:35.009942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b55e44f7152e'
down_revision: Union[str, Sequence[str], None] = ('7dcec49dc4bb', '90f5d6fcecb1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
