"""rename MOTHER to USER role

Revision ID: 146b47073f13
Revises: 91eba63e58ed
Create Date: 2026-07-01 09:32:23.530341

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '146b47073f13'
down_revision: Union[str, Sequence[str], None] = '91eba63e58ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role_enum RENAME VALUE 'MOTHER' TO 'USER'")

def downgrade() -> None:
    op.execute("ALTER TYPE user_role_enum RENAME VALUE 'USER' TO 'MOTHER'")
