"""feat: add labour sessions, readings, alerts, resuscitation logs; update referral model

Revision ID: a1b2c3d4e5f6
Revises: e9f3a2b1c4d5
Create Date: 2026-07-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e9f3a2b1c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'labour_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pregnancy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pregnancy_records.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('clinician_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('active_labour_started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'CLOSED', name='labour_session_status_enum'), nullable=False, server_default='ACTIVE'),
        sa.Column('outcome', sa.Enum('LIVE_BIRTH', 'STILLBIRTH', 'REFERRED', 'OTHER', name='labour_outcome_enum'), nullable=True),
        sa.Column('delivery_type', sa.Enum('VAGINAL', 'C_SECTION', 'ASSISTED', name='labour_delivery_type_enum'), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'labour_readings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('labour_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('type', sa.Enum('DILATION', 'FHR', 'MATERNAL_BP', 'CONTRACTIONS', name='labour_reading_type_enum'), nullable=False, index=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('meta', postgresql.JSON(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'labour_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('labour_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('type', sa.Enum('ACTION_LINE_CROSSED', 'FETAL_DISTRESS', 'PPH_RISK', 'PREECLAMPSIA_RISK', 'SEPSIS_RISK', name='labour_alert_type_enum'), nullable=False),
        sa.Column('severity', sa.Enum('CRITICAL', 'WARNING', name='labour_alert_severity_enum'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('escalated_to', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'resuscitation_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('labour_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('vitals_at_step', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.drop_table('referrals')
    op.execute("DROP TYPE IF EXISTS referral_reason_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS referral_priority_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS referral_status_enum CASCADE")

    op.create_table(
        'referrals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('to_facility_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('from_facility_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('reason', sa.Enum('HEAVY_BLEEDING', 'SEVERE_PAIN', 'REDUCED_FETAL_MOVEMENT', 'LABOUR_STARTED', 'SOMETHING_FEELS_WRONG', 'ROUTINE_TRANSFER', 'SPECIALIST_REFERRAL', name='referral_reason_enum'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_emergency', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('offline_queued', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('client_created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', 'COMPLETED', name='referral_status_enum'), nullable=False, server_default='PENDING'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('referrals')
    op.execute("DROP TYPE IF EXISTS referral_reason_enum")
    op.execute("DROP TYPE IF EXISTS referral_status_enum")

    op.execute("CREATE TYPE referral_reason_enum AS ENUM ('EMERGENCY_COMPLICATION', 'SPECIALIST_CARE', 'LACK_OF_EQUIPMENT', 'PATIENT_PREFERENCE', 'OTHER')")
    op.execute("CREATE TYPE referral_priority_enum AS ENUM ('ROUTINE', 'URGENT', 'EMERGENCY')")
    op.execute("CREATE TYPE referral_status_enum AS ENUM ('PENDING', 'ACCEPTED', 'REJECTED', 'IN_TRANSIT', 'ARRIVED', 'COMPLETED', 'CANCELLED')")

    op.create_table(
        'referrals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sending_facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('receiving_facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('reason', sa.Enum('EMERGENCY_COMPLICATION', 'SPECIALIST_CARE', 'LACK_OF_EQUIPMENT', 'PATIENT_PREFERENCE', 'OTHER', name='referral_reason_enum', create_type=False), nullable=False),
        sa.Column('priority', sa.Enum('ROUTINE', 'URGENT', 'EMERGENCY', name='referral_priority_enum', create_type=False), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', 'IN_TRANSIT', 'ARRIVED', 'COMPLETED', 'CANCELLED', name='referral_status_enum', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('clinical_notes', sa.Text(), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.drop_table('resuscitation_logs')
    op.drop_table('labour_alerts')
    op.drop_table('labour_readings')
    op.drop_table('labour_sessions')

    op.execute("DROP TYPE IF EXISTS labour_alert_severity_enum")
    op.execute("DROP TYPE IF EXISTS labour_alert_type_enum")
    op.execute("DROP TYPE IF EXISTS labour_reading_type_enum")
    op.execute("DROP TYPE IF EXISTS labour_delivery_type_enum")
    op.execute("DROP TYPE IF EXISTS labour_outcome_enum")
    op.execute("DROP TYPE IF EXISTS labour_session_status_enum")
