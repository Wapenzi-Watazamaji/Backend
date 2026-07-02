"""merge facility and cycle tracking migrations

Revision ID: aeb19e697baf
Revises: 89eecf24536a, c06720a2315e
Create Date: 2026-07-01 14:51:25.188130

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aeb19e697baf'
down_revision: Union[str, Sequence[str], None] = ('89eecf24536a', 'c06720a2315e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
