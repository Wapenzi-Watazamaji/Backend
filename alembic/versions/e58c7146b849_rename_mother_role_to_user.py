"""rename_mother_role_to_user

Revision ID: e58c7146b849
Revises: cdbfff70bf80
Create Date: 2026-07-10 09:44:53.485117

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e58c7146b849'
down_revision: Union[str, Sequence[str], None] = 'cdbfff70bf80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migrate any existing users from MOTHER to USER
    op.execute("UPDATE users SET role = 'USER' WHERE role = 'MOTHER';")


def downgrade() -> None:
    # Revert the users back to MOTHER
    op.execute("UPDATE users SET role = 'MOTHER' WHERE role = 'USER';")
