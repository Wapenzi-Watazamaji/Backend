"""merge cycle tracking migrations

Revision ID: 7e4321f3514d
Revises: aeb19e697baf
Create Date: 2026-07-01 14:55:25.860679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e4321f3514d'
down_revision: Union[str, Sequence[str], None] = 'aeb19e697baf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
