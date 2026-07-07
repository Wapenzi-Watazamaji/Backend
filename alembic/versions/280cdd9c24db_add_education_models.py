"""add education models

Revision ID: 280cdd9c24db
Revises: 3d59847aad51
Create Date: 2026-07-02 16:41:51.788617

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '280cdd9c24db'
down_revision: Union[str, Sequence[str], None] = '3d59847aad51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('education_content',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('category', sa.Enum('HYDRATION', 'NUTRITION', 'EXERCISE', 'MENTAL_HEALTH', 'GENERAL', name='content_category_enum'), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('trimester_relevance', sa.JSON(), nullable=False),
    sa.Column('facility_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_education_content_facility_id'), 'education_content', ['facility_id'], unique=False)
    op.create_table('education_events',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('facility_id', sa.UUID(), nullable=False),
    sa.Column('event_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_education_events_facility_id'), 'education_events', ['facility_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_education_events_facility_id'), table_name='education_events')
    op.drop_table('education_events')
    op.drop_index(op.f('ix_education_content_facility_id'), table_name='education_content')
    op.drop_table('education_content')
