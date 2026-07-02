"""change preferred_unit_ids to UUID array

Revision ID: 7a2221338a8e
Revises: 146b47073f13
Create Date: 2026-07-01 11:14:41.548489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '7a2221338a8e'
down_revision: Union[str, Sequence[str], None] = '146b47073f13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'profiles', 'preferred_unit_ids',
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        type_=postgresql.ARRAY(sa.UUID()),
        nullable=True,
        postgresql_using='ARRAY[]::uuid[]',
    )


def downgrade() -> None:
    op.alter_column(
        'profiles', 'preferred_unit_ids',
        existing_type=postgresql.ARRAY(sa.UUID()),
        type_=postgresql.JSON(astext_type=sa.Text()),
        nullable=False,
        postgresql_using="'[]'::json",
    )
