"""merge labour and facility heads

Revision ID: 90f5d6fcecb1
Revises: 3d59847aad51, a1b2c3d4e5f6
Create Date: 2026-07-03 10:37:34.901490

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90f5d6fcecb1'
down_revision: Union[str, Sequence[str], None] = ('3d59847aad51', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
