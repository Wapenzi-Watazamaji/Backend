"""Add missing preferred_unit_ids and other fields to profiles

Revision ID: c5cf4d2e720e
Revises: d4e2f1a3b7c8
Create Date: 2026-07-01 17:05:05.382777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c5cf4d2e720e'
down_revision: Union[str, Sequence[str], None] = 'd4e2f1a3b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # We use server_default='[]' so existing rows get an empty JSON array
    op.add_column('profiles', sa.Column('preferred_unit_ids', sa.JSON(), server_default='[]', nullable=False))
    # op.drop_constraint('profiles_preferred_facility_id_fkey', 'profiles', type_='foreignkey')
    # op.drop_column('profiles', 'preferred_facility_id')


def downgrade() -> None:
    # op.add_column('profiles', sa.Column('preferred_facility_id', sa.UUID(), autoincrement=False, nullable=True))
    # op.create_foreign_key('profiles_preferred_facility_id_fkey', 'profiles', 'facilities', ['preferred_facility_id'], ['id'], ondelete='SET NULL')
    op.drop_column('profiles', 'preferred_unit_ids')

