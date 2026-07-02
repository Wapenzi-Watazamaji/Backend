"""add facility status and is_active columns

Revision ID: 39dcd999938b
Revises: 7a2221338a8e
Create Date: 2026-07-01 11:42:55.799782

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '39dcd999938b'
down_revision: Union[str, Sequence[str], None] = '7a2221338a8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type first
    status_enum = postgresql.ENUM('PENDING_VERIFICATION', 'VERIFIED', 'SUSPENDED', name='facility_status_enum')
    status_enum.create(op.get_bind(), checkfirst=True)
    
    op.add_column('facilities', sa.Column('status', status_enum, nullable=False, server_default='PENDING_VERIFICATION'))
    op.add_column('facilities', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    op.drop_column('facilities', 'is_active')
    op.drop_column('facilities', 'status')
    op.execute("DROP TYPE facility_status_enum")
