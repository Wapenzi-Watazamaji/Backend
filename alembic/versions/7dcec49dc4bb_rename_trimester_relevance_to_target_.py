"""rename trimester_relevance to target_stages

Revision ID: 7dcec49dc4bb
Revises: 280cdd9c24db
Create Date: 2026-07-02 16:54:31.588111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7dcec49dc4bb'
down_revision: Union[str, Sequence[str], None] = '280cdd9c24db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('education_content', sa.Column('target_stages', sa.JSON(), nullable=False))
    op.drop_column('education_content', 'trimester_relevance')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('education_content', sa.Column('trimester_relevance', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False))
    op.drop_column('education_content', 'target_stages')
