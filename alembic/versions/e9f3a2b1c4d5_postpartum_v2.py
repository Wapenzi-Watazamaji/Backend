"""feat: Postpartum v2 - milestones, vaccination records, delivery type enum, new form contexts, seed templates

Revision ID: e9f3a2b1c4d5
Revises: c5cf4d2e720e
Create Date: 2026-07-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, ENUM as PG_ENUM
import uuid
import json
from datetime import datetime, timezone

revision = "e9f3a2b1c4d5"
down_revision = "c5cf4d2e720e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. Extend form_context_enum with new values                        #
    # ------------------------------------------------------------------ #
    op.execute("ALTER TYPE form_context_enum ADD VALUE IF NOT EXISTS 'MATERNAL_CHECKIN'")
    op.execute("COMMIT")
    op.execute("ALTER TYPE form_context_enum ADD VALUE IF NOT EXISTS 'BABY_VITALS'")
    op.execute("COMMIT")

    # ------------------------------------------------------------------ #
    # 2. New enums                                                        #
    # ------------------------------------------------------------------ #
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE delivery_type_enum AS ENUM ('VAGINAL', 'C_SECTION');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE milestone_category_enum AS ENUM ('GROWTH', 'MOVEMENT', 'FEEDING', 'SLEEP', 'FIRST_MOMENTS');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # ------------------------------------------------------------------ #
    # 3. Alter existing baby_profiles to add missing columns             #
    # ------------------------------------------------------------------ #
    op.add_column("baby_profiles", sa.Column("time_of_birth", sa.Time(), nullable=True))
    op.add_column("baby_profiles", sa.Column(
        "delivery_type",
        PG_ENUM("VAGINAL", "C_SECTION", name="delivery_type_enum", create_type=False),
        nullable=True,
    ))
    op.add_column("baby_profiles", sa.Column("birth_length_cm", sa.Float(), nullable=True))
    op.add_column("baby_profiles", sa.Column("place_of_birth", sa.String(), nullable=True))

    # ------------------------------------------------------------------ #
    # 4. Create new tables                                                #
    # ------------------------------------------------------------------ #
    op.create_table(
        "baby_milestones",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("baby_id", UUID(as_uuid=True), sa.ForeignKey("baby_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("category", PG_ENUM("GROWTH", "MOVEMENT", "FEEDING", "SLEEP", "FIRST_MOMENTS", name="milestone_category_enum", create_type=False), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("achieved_at", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("photo_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "baby_vaccination_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("baby_id", UUID(as_uuid=True), sa.ForeignKey("baby_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("scheduled_visit_id", UUID(as_uuid=True), sa.ForeignKey("scheduled_visits.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("vaccine_id", sa.String(), nullable=False),
        sa.Column("given_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("facility_id", sa.String(), nullable=True),
        sa.Column("batch_number", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ------------------------------------------------------------------ #
    # 5. Seed: MOH Vaccination Pathway Template                          #
    # ------------------------------------------------------------------ #
    vaccination_milestones = [
        {"order": 1, "vaccineId": "vac_bcg",  "label": "BCG",                  "ageMilestone": "At birth",  "triggerWeek": 0},
        {"order": 2, "vaccineId": "vac_opv0", "label": "OPV 0 (birth dose)",   "ageMilestone": "At birth",  "triggerWeek": 0},
        {"order": 3, "vaccineId": "vac_hepb0","label": "Hep B (birth dose)",   "ageMilestone": "At birth",  "triggerWeek": 0},
        {"order": 4, "vaccineId": "vac_opv1", "label": "OPV 1",                "ageMilestone": "6 weeks",   "triggerWeek": 6},
        {"order": 5, "vaccineId": "vac_dpt1", "label": "DPT-HepB-Hib (1st)",  "ageMilestone": "6 weeks",   "triggerWeek": 6},
        {"order": 6, "vaccineId": "vac_pcv1", "label": "PCV (1st dose)",       "ageMilestone": "6 weeks",   "triggerWeek": 6},
        {"order": 7, "vaccineId": "vac_rota1","label": "Rotavirus (1st dose)", "ageMilestone": "6 weeks",   "triggerWeek": 6},
        {"order": 8, "vaccineId": "vac_opv2", "label": "OPV 2",                "ageMilestone": "10 weeks",  "triggerWeek": 10},
        {"order": 9, "vaccineId": "vac_dpt2", "label": "DPT-HepB-Hib (2nd)",  "ageMilestone": "10 weeks",  "triggerWeek": 10},
        {"order":10, "vaccineId": "vac_pcv2", "label": "PCV (2nd dose)",       "ageMilestone": "10 weeks",  "triggerWeek": 10},
        {"order":11, "vaccineId": "vac_rota2","label": "Rotavirus (2nd dose)", "ageMilestone": "10 weeks",  "triggerWeek": 10},
        {"order":12, "vaccineId": "vac_opv3", "label": "OPV 3",                "ageMilestone": "14 weeks",  "triggerWeek": 14},
        {"order":13, "vaccineId": "vac_dpt3", "label": "DPT-HepB-Hib (3rd)",  "ageMilestone": "14 weeks",  "triggerWeek": 14},
        {"order":14, "vaccineId": "vac_pcv3", "label": "PCV (3rd dose)",       "ageMilestone": "14 weeks",  "triggerWeek": 14},
        {"order":15, "vaccineId": "vac_ipv",  "label": "IPV",                  "ageMilestone": "14 weeks",  "triggerWeek": 14},
        {"order":16, "vaccineId": "vac_mr",   "label": "Measles-Rubella",      "ageMilestone": "9 months",  "triggerWeek": 39},
        {"order":17, "vaccineId": "vac_vita", "label": "Vitamin A (1st)",      "ageMilestone": "9 months",  "triggerWeek": 39},
        {"order":18, "vaccineId": "vac_mr2",  "label": "MR (booster)",         "ageMilestone": "18 months", "triggerWeek": 78},
    ]
    op.execute(
        sa.text("""
            INSERT INTO care_pathway_templates (id, name, description, milestones, is_active)
            VALUES (:id, :name, :description, CAST(:milestones AS JSON), :is_active)
            ON CONFLICT (id) DO NOTHING
        """).bindparams(
            id="path_vaccination_moh_v1",
            name="MOH Infant Immunisation Schedule",
            description="Kenya Ministry of Health recommended infant vaccination schedule",
            milestones=json.dumps(vaccination_milestones),
            is_active=True,
        )
    )

    # ------------------------------------------------------------------ #
    # 6. Seed: MOH Postnatal Visit Pathway Template                      #
    # ------------------------------------------------------------------ #
    postnatal_milestones = [
        {"order": 1, "label": "48-hour check",     "triggerDays": 2,  "covers": ["MOTHER", "BABY"], "description": "Early postnatal assessment — bleeding, feeding, jaundice screen"},
        {"order": 2, "label": "1-week check",      "triggerDays": 7,  "covers": ["MOTHER", "BABY"], "description": "Weight check, wound review, breastfeeding support"},
        {"order": 3, "label": "6-week check",      "triggerDays": 42, "covers": ["MOTHER", "BABY"], "description": "Full postnatal discharge review, EPDS screen, contraception counselling"},
    ]
    op.execute(
        sa.text("""
            INSERT INTO care_pathway_templates (id, name, description, milestones, is_active)
            VALUES (:id, :name, :description, CAST(:milestones AS JSON), :is_active)
            ON CONFLICT (id) DO NOTHING
        """).bindparams(
            id="path_postnatal_moh_v1",
            name="MOH Postnatal Visit Schedule",
            description="WHO/MOH recommended mother and baby postnatal check-up schedule",
            milestones=json.dumps(postnatal_milestones),
            is_active=True,
        )
    )

    # ------------------------------------------------------------------ #
    # 7. Seed: Maternal Check-in Form Template                           #
    # ------------------------------------------------------------------ #
    maternal_checkin_template = {
        "fields": [
            {
                "key": "physicalSymptoms",
                "label": "How are you feeling physically?",
                "type": "MULTI_SELECT",
                "required": True,
                "options": [
                    "BLEEDING_REDUCED", "HEAVY_BLEEDING", "PAIN_AT_SITE",
                    "SWELLING", "FEVER_OR_CHILLS", "BREAST_TENDERNESS", "FEELING_WELL"
                ],
                "flaggingOptions": {"flagValues": ["HEAVY_BLEEDING", "FEVER_OR_CHILLS"]},
            },
            {
                "key": "mood",
                "label": "How is your mood today?",
                "type": "SINGLE_SELECT",
                "required": True,
                "options": ["VERY_GOOD", "GOOD", "NEUTRAL", "LOW", "VERY_LOW"],
                "flaggingOptions": {"flagValues": ["VERY_LOW"]},
            },
            {
                "key": "notes",
                "label": "Any other notes",
                "type": "TEXT",
                "required": False,
            },
        ]
    }
    op.execute(
        sa.text("""
            INSERT INTO form_templates (id, slug, context, fields, version, is_active)
            VALUES (CAST(:id AS UUID), :slug, CAST(:context AS form_context_enum), CAST(:fields AS JSON), :version, :is_active)
            ON CONFLICT DO NOTHING
        """).bindparams(
            id=str(uuid.uuid4()),
            slug="tmpl_maternal_checkin_v1",
            context="MATERNAL_CHECKIN",
            fields=json.dumps(maternal_checkin_template),
            version="v1",
            is_active=True,
        )
    )

    # ------------------------------------------------------------------ #
    # 8. Seed: Baby Vitals Form Template                                 #
    # ------------------------------------------------------------------ #
    baby_vitals_template = {
        "fields": [
            {
                "key": "temperatureCelsius",
                "label": "Temperature (°C)",
                "type": "NUMBER",
                "required": True,
                "flaggingOptions": {"min": 36.0, "max": 38.0},
            },
            {
                "key": "spo2Percent",
                "label": "SpO2 (%)",
                "type": "NUMBER",
                "required": False,
                "flaggingOptions": {"min": 94},
            },
            {
                "key": "feedingType",
                "label": "Feeding type",
                "type": "SINGLE_SELECT",
                "required": True,
                "options": ["BREASTFEEDING", "FORMULA", "BOTH"],
            },
            {
                "key": "feedCountToday",
                "label": "Number of feeds today",
                "type": "NUMBER",
                "required": True,
                "flaggingOptions": {"min": 6},
            },
            {
                "key": "symptoms",
                "label": "Any symptoms?",
                "type": "MULTI_SELECT",
                "required": True,
                "options": [
                    "DIFFICULTY_BREATHING", "UNUSUALLY_SLEEPY", "POOR_FEEDING",
                    "JAUNDICE", "FEVER", "COLD_TO_TOUCH", "ALL_NORMAL"
                ],
                "flaggingOptions": {
                    "flagValues": [
                        "DIFFICULTY_BREATHING", "UNUSUALLY_SLEEPY", "POOR_FEEDING",
                        "JAUNDICE", "FEVER", "COLD_TO_TOUCH"
                    ]
                },
            },
            {
                "key": "notes",
                "label": "Notes",
                "type": "TEXT",
                "required": False,
            },
        ]
    }
    op.execute(
        sa.text("""
            INSERT INTO form_templates (id, slug, context, fields, version, is_active)
            VALUES (CAST(:id AS UUID), :slug, CAST(:context AS form_context_enum), CAST(:fields AS JSON), :version, :is_active)
            ON CONFLICT DO NOTHING
        """).bindparams(
            id=str(uuid.uuid4()),
            slug="tmpl_baby_vitals_v1",
            context="BABY_VITALS",
            fields=json.dumps(baby_vitals_template),
            version="v1",
            is_active=True,
        )
    )


def downgrade() -> None:
    op.drop_table("baby_vaccination_records")
    op.drop_table("baby_milestones")
    op.drop_column("baby_profiles", "place_of_birth")
    op.drop_column("baby_profiles", "birth_length_cm")
    op.drop_column("baby_profiles", "delivery_type")
    op.drop_column("baby_profiles", "time_of_birth")
    op.execute("DROP TYPE IF EXISTS milestone_category_enum")
    op.execute("DROP TYPE IF EXISTS delivery_type_enum")
