"""seed pitch demo data: Margret Nkatha end-to-end story + education content

Seeds a single, richly-detailed mother-facing demo user (Margret Nkatha) covering
Auth -> Profile -> Cycle Tracking -> Pregnancy #1 (historical) -> Postpartum &
Baby Tracker -> Pregnancy #2 (active), per docs/seed-data-margret-nkatha.md, plus
a broad set of education content/events so the mobile Feed is never empty.

All primary keys are generated with uuid.uuid4() in Python and reused for every
FK reference within this migration (mirroring how the real API would hand back
generated IDs). Enum/JSON/JSONB/UUID/ARRAY columns are bound through lightweight
Core `table()` objects with proper SQLAlchemy types so the asyncpg driver
receives correctly-typed parameters (the same mechanism the ORM relies on at
runtime), instead of hand-written CAST() strings.

This migration is idempotent: if the demo user's phone number already exists,
upgrade() is a no-op.

Revision ID: f82058260ce1
Revises: 6afe51263409
Create Date: 2026-07-21
"""
from datetime import date, datetime, time, timezone, timedelta
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column, insert, select
from sqlalchemy.dialects import postgresql as pg

from app.core.security import get_password_hash

# revision identifiers, used by Alembic.
revision: str = "f82058260ce1"
down_revision: str | None = "6afe51263409"
branch_labels: str | None = None
depends_on: str | None = None


# --------------------------------------------------------------------------- #
# Fixed demo identifiers (used for idempotency checks + a clean downgrade)     #
# --------------------------------------------------------------------------- #
NKATHA_PHONE = "+254798651234"  # +254720168641 from the source doc is already taken by an unrelated account
CLINICIAN_PHONE = "+254711992244"
FACILITY_NAME = "Meru Teaching and Referral Hospital"
FACILITY_COUNTY = "Meru"

UTC = timezone.utc


def _dt(y, m, d, hh=0, mm=0, ss=0) -> datetime:
    return datetime(y, m, d, hh, mm, ss, tzinfo=UTC)


def _midnight(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=UTC)


# --------------------------------------------------------------------------- #
# Lightweight Core table() definitions (typed, so asyncpg gets correct binds) #
# --------------------------------------------------------------------------- #

def _t(name, *cols):
    return table(name, *cols)


users_t = _t(
    "users",
    column("id", pg.UUID(as_uuid=True)),
    column("phone_number", sa.String),
    column("password_hash", sa.String),
    column("role", pg.ENUM(name="user_role_enum", create_type=False)),
    column("account_type", pg.ENUM(name="account_type_enum", create_type=False)),
    column("full_name", sa.String),
    column("date_of_birth", sa.Date),
    column("gender", pg.ENUM(name="gender_enum", create_type=False)),
    column("preferred_language", sa.String),
    column("county", sa.String),
    column("profile_photo_url", sa.String),
    column("is_active", sa.Boolean),
    column("created_at", sa.DateTime(timezone=True)),
    column("updated_at", sa.DateTime(timezone=True)),
)

profiles_t = _t(
    "profiles",
    column("id", pg.UUID(as_uuid=True)),
    column("user_id", pg.UUID(as_uuid=True)),
    column("current_stage", pg.ENUM(name="current_stage_enum", create_type=False)),
    column("preferred_facility_id", pg.UUID(as_uuid=True)),
    column("emergency_sharing_preference", pg.ENUM(name="sharing_pref_enum", create_type=False)),
    column("notification_preference", pg.ENUM(name="notification_pref_enum", create_type=False)),
    column("emergency_contact_name", sa.String),
    column("emergency_contact_relationship", sa.String),
    column("emergency_contact_phone", sa.String),
    column("companion_preference", pg.ENUM(name="companion_pref_enum", create_type=False)),
    column("home_address_name", sa.String),
    column("home_location_lat", sa.String),
    column("home_location_lng", sa.String),
    column("live_location_sharing_enabled", sa.Boolean),
    column("typical_cycle_length_days", sa.Integer),
    column("personal_doctor_id", pg.UUID(as_uuid=True)),
    column("personal_doctor_request_status", pg.ENUM(name="doctor_req_status_enum", create_type=False)),
    column("qr_passport_token", sa.String),
    column("created_at", sa.DateTime(timezone=True)),
    column("updated_at", sa.DateTime(timezone=True)),
)

facilities_t = _t(
    "facilities",
    column("id", pg.UUID(as_uuid=True)),
    column("name", sa.String),
    column("type", pg.ENUM(name="facility_type_enum", create_type=False)),
    column("county", sa.String),
    column("address", sa.String),
    column("phone_number", sa.String),
    column("email", sa.String),
    column("latitude", sa.Float),
    column("longitude", sa.Float),
    column("status", pg.ENUM(name="facility_status_enum", create_type=False)),
    column("is_active", sa.Boolean),
    column("services_offered", pg.ARRAY(sa.String)),
    column("readiness", sa.JSON),
    column("updated_at", sa.DateTime(timezone=True)),
)

staff_members_t = _t(
    "staff_members",
    column("id", pg.UUID(as_uuid=True)),
    column("facility_id", pg.UUID(as_uuid=True)),
    column("user_id", pg.UUID(as_uuid=True)),
    column("role", pg.ENUM(name="staff_role_enum", create_type=False)),
    column("specialty", sa.String),
    column("assigned_patient_count", sa.Integer),
    column("status", pg.ENUM(name="staff_status_enum", create_type=False)),
    column("is_on_duty", sa.Boolean),
    column("invited_at", sa.DateTime(timezone=True)),
    column("joined_at", sa.DateTime(timezone=True)),
)

medical_history_t = _t(
    "medical_history_records",
    column("id", pg.UUID(as_uuid=True)),
    column("patient_user_id", pg.UUID(as_uuid=True)),
    column("created_by", pg.UUID(as_uuid=True)),
    column("last_updated_by", pg.UUID(as_uuid=True)),
    column("blood_type", sa.String),
    column("rh_factor", sa.String),
    column("allergies", pg.ARRAY(sa.String)),
    column("chronic_conditions", pg.ARRAY(sa.String)),
    column("current_medications", pg.JSONB),
    column("surgical_history", pg.JSONB),
    column("previous_pregnancies", sa.Integer),
    column("previous_outcomes", pg.ARRAY(sa.String)),
    column("family_history", pg.ARRAY(sa.String)),
    column("custom_fields", pg.JSONB),
    column("created_at", sa.DateTime(timezone=True)),
    column("updated_at", sa.DateTime(timezone=True)),
)

form_templates_t = _t(
    "form_templates",
    column("id", pg.UUID(as_uuid=True)),
    column("slug", sa.String),
    column("context", pg.ENUM(name="form_context_enum", create_type=False)),
    column("fields", sa.JSON),
    column("version", sa.String),
    column("is_active", sa.Boolean),
    column("facility_id", pg.UUID(as_uuid=True)),
    column("created_at", sa.DateTime(timezone=True)),
)

form_submissions_t = _t(
    "form_submissions",
    column("id", pg.UUID(as_uuid=True)),
    column("template_id", pg.UUID(as_uuid=True)),
    column("user_id", pg.UUID(as_uuid=True)),
    column("context", pg.ENUM(name="form_context_enum", create_type=False)),
    column("answers", sa.JSON),
    column("client_generated_id", sa.String),
    column("client_created_at", sa.DateTime(timezone=True)),
    column("created_at", sa.DateTime(timezone=True)),
    column("updated_at", sa.DateTime(timezone=True)),
)

cycle_entries_t = _t(
    "cycle_entries",
    column("id", pg.UUID(as_uuid=True)),
    column("user_id", pg.UUID(as_uuid=True)),
    column("submission_id", pg.UUID(as_uuid=True)),
    column("start_date", sa.Date),
    column("end_date", sa.Date),
    column("pbac_score", sa.Integer),
    column("created_at", sa.DateTime(timezone=True)),
    column("updated_at", sa.DateTime(timezone=True)),
)

pbac_items_t = _t(
    "pbac_items",
    column("id", pg.UUID(as_uuid=True)),
    column("cycle_entry_id", pg.UUID(as_uuid=True)),
    column("date", sa.Date),
    column("item_type", pg.ENUM(name="pbac_item_type_enum", create_type=False)),
    column("soak_level", pg.ENUM(name="pbac_soak_level_enum", create_type=False)),
    column("point_value", sa.Integer),
    column("created_at", sa.DateTime(timezone=True)),
)

pregnancy_records_t = _t(
    "pregnancy_records",
    column("id", pg.UUID(as_uuid=True)),
    column("user_id", pg.UUID(as_uuid=True)),
    column("last_menstrual_period", sa.Date),
    column("due_date", sa.Date),
    column("is_first_pregnancy", sa.Boolean),
    column("status", pg.ENUM(name="pregnancy_status_enum", create_type=False)),
    column("outcome", pg.ENUM(name="pregnancy_outcome_enum", create_type=False)),
    column("ended_at", sa.DateTime(timezone=True)),
    column("created_at", sa.DateTime(timezone=True)),
    column("updated_at", sa.DateTime(timezone=True)),
)

scheduled_visits_t = _t(
    "scheduled_visits",
    column("id", pg.UUID(as_uuid=True)),
    column("pregnancy_id", pg.UUID(as_uuid=True)),
    column("baby_id", pg.UUID(as_uuid=True)),
    column("pathway_template_id", sa.String),
    column("milestone_order", sa.Integer),
    column("label", sa.String),
    column("scheduled_at", sa.DateTime(timezone=True)),
    column("status", pg.ENUM(name="visit_status_enum", create_type=False)),
    column("facility_id", pg.UUID(as_uuid=True)),
    column("purpose", sa.Text),
    column("summary", sa.Text),
    column("created_at", sa.DateTime(timezone=True)),
    column("updated_at", sa.DateTime(timezone=True)),
)

pregnancy_vitals_entries_t = _t(
    "pregnancy_vitals_entries",
    column("id", pg.UUID(as_uuid=True)),
    column("pregnancy_id", pg.UUID(as_uuid=True)),
    column("submission_id", pg.UUID(as_uuid=True)),
    column("is_flagged", sa.Boolean),
    column("flagged_reasons", sa.JSON),
    column("created_at", sa.DateTime(timezone=True)),
    column("updated_at", sa.DateTime(timezone=True)),
)

pregnancy_risk_scores_t = _t(
    "pregnancy_risk_scores",
    column("id", pg.UUID(as_uuid=True)),
    column("pregnancy_id", pg.UUID(as_uuid=True)),
    column("user_id", pg.UUID(as_uuid=True)),
    column("score", sa.Integer),
    column("level", pg.ENUM(name="risk_level_enum", create_type=False)),
    column("factors", sa.JSON),
    column("clinician_override", sa.JSON),
    column("calculated_at", sa.DateTime(timezone=True)),
)

baby_profiles_t = _t(
    "baby_profiles",
    column("id", pg.UUID(as_uuid=True)),
    column("user_id", pg.UUID(as_uuid=True)),
    column("pregnancy_id", pg.UUID(as_uuid=True)),
    column("name", sa.String),
    column("date_of_birth", sa.Date),
    column("time_of_birth", sa.Time),
    column("gender", pg.ENUM(name="baby_gender_enum", create_type=False)),
    column("delivery_type", pg.ENUM(name="delivery_type_enum", create_type=False)),
    column("birth_weight_kg", sa.Float),
    column("birth_length_cm", sa.Float),
    column("place_of_birth", sa.String),
    column("notes", sa.Text),
    column("created_at", sa.DateTime(timezone=True)),
    column("updated_at", sa.DateTime(timezone=True)),
)

baby_milestones_t = _t(
    "baby_milestones",
    column("id", pg.UUID(as_uuid=True)),
    column("baby_id", pg.UUID(as_uuid=True)),
    column("user_id", pg.UUID(as_uuid=True)),
    column("category", pg.ENUM(name="milestone_category_enum", create_type=False)),
    column("title", sa.String),
    column("achieved_at", sa.Date),
    column("note", sa.Text),
    column("photo_url", sa.String),
    column("created_at", sa.DateTime(timezone=True)),
)

baby_vaccination_records_t = _t(
    "baby_vaccination_records",
    column("id", pg.UUID(as_uuid=True)),
    column("baby_id", pg.UUID(as_uuid=True)),
    column("scheduled_visit_id", pg.UUID(as_uuid=True)),
    column("vaccine_id", sa.String),
    column("given_at", sa.DateTime(timezone=True)),
    column("facility_id", sa.String),
    column("batch_number", sa.String),
    column("created_at", sa.DateTime(timezone=True)),
)

epds_screenings_t = _t(
    "epds_screenings",
    column("id", pg.UUID(as_uuid=True)),
    column("user_id", pg.UUID(as_uuid=True)),
    column("answers", sa.JSON),
    column("total_score", sa.Integer),
    column("q10_score", sa.Integer),
    column("is_self_harm_flagged", sa.Boolean),
    column("risk_level", pg.ENUM(name="epds_risk_level_enum", create_type=False)),
    column("created_at", sa.DateTime(timezone=True)),
)

education_content_t = _t(
    "education_content",
    column("id", pg.UUID(as_uuid=True)),
    column("title", sa.String),
    column("category", pg.ENUM(name="content_category_enum", create_type=False)),
    column("body", sa.Text),
    column("target_stages", sa.JSON),
    column("facility_id", pg.UUID(as_uuid=True)),
    column("created_at", sa.DateTime(timezone=True)),
    column("updated_at", sa.DateTime(timezone=True)),
)

education_events_t = _t(
    "education_events",
    column("id", pg.UUID(as_uuid=True)),
    column("title", sa.String),
    column("facility_id", pg.UUID(as_uuid=True)),
    column("event_date", sa.DateTime(timezone=True)),
    column("description", sa.Text),
    column("created_at", sa.DateTime(timezone=True)),
    column("updated_at", sa.DateTime(timezone=True)),
)

care_pathway_templates_t = _t(
    "care_pathway_templates",
    column("id", sa.String),
    column("milestones", sa.JSON),
)


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _get_pathway_milestones(conn, pathway_id: str) -> list[dict]:
    row = conn.execute(
        select(care_pathway_templates_t.c.milestones).where(care_pathway_templates_t.c.id == pathway_id)
    ).fetchone()
    return row[0] if row and row[0] else []


def _ensure_form_template(conn, context: str, preferred_slug: str, fields: dict) -> uuid.UUID:
    """
    Prefer an exact slug match, then any active template for the context
    (whatever a prior deploy/seed script already put there), and only create
    a brand-new one (with the doc-correct field keys) if nothing exists yet.
    """
    row = conn.execute(select(form_templates_t.c.id).where(form_templates_t.c.slug == preferred_slug)).fetchone()
    if row:
        return row[0]

    row = conn.execute(
        select(form_templates_t.c.id)
        .where(form_templates_t.c.context == context, form_templates_t.c.is_active == True)  # noqa: E712
        .order_by(form_templates_t.c.created_at.desc())
        .limit(1)
    ).fetchone()
    if row:
        return row[0]

    new_id = uuid.uuid4()
    conn.execute(
        insert(form_templates_t).values(
            id=new_id,
            slug=preferred_slug,
            context=context,
            fields=fields,
            version="v1",
            is_active=True,
            facility_id=None,
            created_at=datetime.now(UTC),
        )
    )
    return new_id


def upgrade() -> None:
    conn = op.get_bind()

    existing = conn.execute(select(users_t.c.id).where(users_t.c.phone_number == NKATHA_PHONE)).fetchone()
    if existing:
        print(f"Demo user {NKATHA_PHONE} already exists — skipping seed (idempotent no-op).")
        return

    # ----------------------------------------------------------------- #
    # 1. Facility                                                        #
    # ----------------------------------------------------------------- #
    facility_row = conn.execute(
        select(facilities_t.c.id).where(
            facilities_t.c.name == FACILITY_NAME, facilities_t.c.county == FACILITY_COUNTY
        )
    ).fetchone()

    if facility_row:
        facility_id = facility_row[0]
    else:
        facility_id = uuid.uuid4()
        conn.execute(
            insert(facilities_t).values(
                id=facility_id,
                name=FACILITY_NAME,
                type="PUBLIC",
                county=FACILITY_COUNTY,
                address="Meru–Nkubu Rd, Meru Town",
                phone_number="+254612030150",
                email=None,
                latitude=0.0470,
                longitude=37.6559,
                status="VERIFIED",
                is_active=True,
                services_offered=["ANTENATAL_CARE", "DELIVERY", "POSTNATAL_CARE", "IMMUNIZATION"],
                readiness={"bloodBankStocked": True, "maternityBedsAvailable": 20},
                updated_at=datetime.now(UTC),
            )
        )

    # ----------------------------------------------------------------- #
    # 2. Auth — Margret Nkatha + a clinician (record author for          #
    #    medical-history / vaccination-facility references)              #
    # ----------------------------------------------------------------- #
    nkatha_id = uuid.uuid4()
    clinician_id = uuid.uuid4()
    member_since = _dt(2024, 3, 20, 8, 0)

    conn.execute(
        insert(users_t),
        [
            {
                "id": nkatha_id,
                "phone_number": NKATHA_PHONE,
                "password_hash": get_password_hash("Nkatha@55"),
                "role": "USER",
                "account_type": "FULL",
                "full_name": "Margret Nkatha",
                "date_of_birth": date(1996, 4, 18),
                "gender": "FEMALE",
                "preferred_language": "en",
                "county": "Meru",
                "profile_photo_url": None,
                "is_active": True,
                "created_at": member_since,
                "updated_at": member_since,
            },
            {
                "id": clinician_id,
                "phone_number": CLINICIAN_PHONE,
                "password_hash": None,
                "role": "CLINICIAN",
                "account_type": "FULL",
                "full_name": "Dr. Wanjiru Kiptoo",
                "date_of_birth": date(1985, 2, 11),
                "gender": "FEMALE",
                "preferred_language": "en",
                "county": "Meru",
                "profile_photo_url": None,
                "is_active": True,
                "created_at": _dt(2024, 1, 10, 8, 0),
                "updated_at": _dt(2024, 1, 10, 8, 0),
            },
        ],
    )

    conn.execute(
        insert(staff_members_t).values(
            id=uuid.uuid4(),
            facility_id=facility_id,
            user_id=clinician_id,
            role="CLINICIAN",
            specialty="Obstetrics & Gynaecology",
            assigned_patient_count=1,
            status="ACTIVE",
            is_on_duty=True,
            invited_at=_dt(2024, 1, 10, 8, 0),
            joined_at=_dt(2024, 1, 12, 8, 0),
        )
    )

    # ----------------------------------------------------------------- #
    # 3. Profile + medical history                                       #
    # ----------------------------------------------------------------- #
    conn.execute(
        insert(profiles_t).values(
            id=uuid.uuid4(),
            user_id=nkatha_id,
            current_stage="PREGNANT",
            preferred_facility_id=facility_id,
            emergency_sharing_preference="ALWAYS_SHARE",
            notification_preference="BOTH",
            emergency_contact_name="Kaburu Mwenda",
            emergency_contact_relationship="Husband",
            emergency_contact_phone="+254733221144",
            companion_preference="BOTH",
            home_address_name="Kaaga, Meru Town",
            home_location_lat="0.0470",
            home_location_lng="37.6559",
            live_location_sharing_enabled=True,
            typical_cycle_length_days=29,
            personal_doctor_id=None,
            personal_doctor_request_status="PENDING",
            qr_passport_token=None,
            created_at=_dt(2024, 3, 20, 8, 5),
            updated_at=datetime.now(UTC),
        )
    )

    conn.execute(
        insert(medical_history_t).values(
            id=uuid.uuid4(),
            patient_user_id=nkatha_id,
            created_by=clinician_id,
            last_updated_by=clinician_id,
            blood_type="O",
            rh_factor="+",
            allergies=[],
            chronic_conditions=[],
            current_medications=[
                {"name": "Folic acid", "dose": "5mg", "frequency": "daily"},
                {"name": "Ferrous sulphate", "dose": "200mg", "frequency": "daily"},
            ],
            surgical_history=[],
            previous_pregnancies=1,
            previous_outcomes=["LIVE_BIRTH"],
            family_history=["Hypertension — maternal grandmother"],
            custom_fields=None,
            created_at=_dt(2025, 5, 16, 10, 0),
            updated_at=_dt(2025, 5, 16, 10, 0),
        )
    )

    # ----------------------------------------------------------------- #
    # Form templates used throughout (create only if truly missing)      #
    # ----------------------------------------------------------------- #
    cycle_entry_tmpl = _ensure_form_template(
        conn, "CYCLE_ENTRY", "tmpl_cycle_entry_v1",
        {"fields": [
            {"key": "flowLevel", "label": "Flow", "type": "SINGLE_SELECT", "required": True,
             "options": ["LIGHT", "MODERATE", "HEAVY", "VERY_HEAVY"]},
            {"key": "clotLevel", "label": "Clots", "type": "SINGLE_SELECT", "required": False,
             "options": ["NONE", "SMALL", "LARGE"]},
            {"key": "flags", "label": "Additional flags", "type": "MULTI_SELECT", "required": False,
             "options": ["LEAKED_THROUGH_CLOTHING", "CHANGED_AT_NIGHT", "SOAKED_WITHIN_2_HOURS"]},
        ]},
    )
    cycle_symptom_tmpl = _ensure_form_template(
        conn, "CYCLE_SYMPTOM", "tmpl_symptom_entry_v1",
        {"fields": [
            {"key": "symptoms", "label": "Symptoms", "type": "MULTI_SELECT", "required": True,
             "options": ["CRAMPS", "BLOATING", "MOOD_SWINGS", "FATIGUE", "HEADACHE", "NAUSEA"]},
            {"key": "notes", "label": "Notes", "type": "TEXT", "required": False},
        ]},
    )
    preg_vitals_tmpl = _ensure_form_template(
        conn, "PREGNANCY_VITALS", "tmpl_preg_vitals_v1",
        {"fields": [
            {"key": "systolicBp", "label": "Systolic BP", "type": "NUMBER", "unit": "mmHg", "required": True,
             "flaggingOptions": {"max": 140}},
            {"key": "diastolicBp", "label": "Diastolic BP", "type": "NUMBER", "unit": "mmHg", "required": True,
             "flaggingOptions": {"max": 90}},
            {"key": "weightKg", "label": "Weight", "type": "NUMBER", "unit": "kg", "required": True},
            {"key": "symptoms", "label": "Symptoms", "type": "MULTI_SELECT", "required": False,
             "options": ["NAUSEA", "BACK_PAIN", "SWELLING", "HEADACHE", "FATIGUE"]},
        ]},
    )
    maternal_checkin_tmpl = _ensure_form_template(
        conn, "MATERNAL_CHECKIN", "tmpl_postpartum_checkin_v1",
        {"fields": [
            {"key": "bleedingLevel", "label": "Bleeding", "type": "SINGLE_SELECT", "required": True,
             "options": ["NONE", "LIGHT", "MODERATE", "HEAVY"]},
            {"key": "painLevel", "label": "Pain (0-10)", "type": "NUMBER", "required": True},
            {"key": "symptoms", "label": "Symptoms", "type": "MULTI_SELECT", "required": False,
             "options": ["FATIGUE", "CRAMPING", "FEVER", "HEADACHE"]},
        ]},
    )
    baby_vitals_tmpl = _ensure_form_template(
        conn, "BABY_VITALS", "tmpl_baby_vitals_v1",
        {"fields": [
            {"key": "temperatureCelsius", "label": "Temperature (°C)", "type": "NUMBER", "required": True,
             "flaggingOptions": {"min": 36.0, "max": 38.0}},
            {"key": "feedingType", "label": "Feeding type", "type": "SINGLE_SELECT", "required": True,
             "options": ["BREASTFEEDING", "FORMULA", "BOTH"]},
            {"key": "feedCountToday", "label": "Feeds today", "type": "NUMBER", "required": True},
            {"key": "symptoms", "label": "Symptoms", "type": "MULTI_SELECT", "required": True,
             "options": ["DIFFICULTY_BREATHING", "UNUSUALLY_SLEEPY", "POOR_FEEDING", "JAUNDICE", "FEVER",
                         "COLD_TO_TOUCH", "ALL_NORMAL"]},
        ]},
    )

    # ----------------------------------------------------------------- #
    # 4.1 Cycle tracking — Phase A (pre-Pregnancy #1)                    #
    # ----------------------------------------------------------------- #
    cycle_a = [
        {"ref": "cycleA1", "start": date(2024, 4, 2), "flow": "MODERATE", "clot": "NONE", "flags": []},
        {"ref": "cycleA2", "start": date(2024, 5, 1), "flow": "HEAVY", "clot": "SMALL", "flags": []},
        {"ref": "cycleA3", "start": date(2024, 5, 30), "flow": "MODERATE", "clot": "NONE", "flags": []},
        {"ref": "cycleA4", "start": date(2024, 6, 28), "flow": "MODERATE", "clot": "NONE", "flags": []},
        {"ref": "cycleA5", "start": date(2024, 8, 1), "flow": "LIGHT", "clot": "NONE", "flags": []},
    ]
    cycle_a_entry_ids = _seed_cycle_entries(conn, nkatha_id, cycle_entry_tmpl, cycle_a)

    # PBAC items — cycleA2 (3-day heavy period) and cycleA4
    _seed_pbac_items(conn, cycle_a_entry_ids["cycleA2"], [
        (date(2024, 5, 1), "FULLY_SOAKED", 20),
        (date(2024, 5, 2), "MODERATELY_SOAKED", 5),
        (date(2024, 5, 3), "LIGHTLY_SOAKED", 1),
    ])
    _seed_pbac_items(conn, cycle_a_entry_ids["cycleA4"], [
        (date(2024, 6, 28), "MODERATELY_SOAKED", 5),
        (date(2024, 6, 29), "LIGHTLY_SOAKED", 1),
    ])

    symptoms_a = [
        (date(2024, 4, 2), ["CRAMPS", "BLOATING"], "Mild cramps, manageable"),
        (date(2024, 4, 29), ["MOOD_SWINGS"], "A bit irritable before period"),
        (date(2024, 5, 1), ["CRAMPS", "FATIGUE"], "Heavier flow today"),
        (date(2024, 5, 30), ["BLOATING"], None),
        (date(2024, 6, 26), ["HEADACHE"], "Mild headache, 2 days before period"),
        (date(2024, 6, 28), ["CRAMPS"], None),
        (date(2024, 8, 1), ["FATIGUE", "NAUSEA"], "Felt off, later found out I was pregnant"),
    ]
    _seed_symptoms(conn, nkatha_id, cycle_symptom_tmpl, symptoms_a)

    # ----------------------------------------------------------------- #
    # 5.1 Pregnancy #1 — historical, ended in a live birth               #
    # ----------------------------------------------------------------- #
    pregnancy1_id = uuid.uuid4()
    lmp1 = date(2024, 8, 1)
    due1 = lmp1 + timedelta(days=280)
    ended_at = _dt(2025, 5, 14, 11, 20)

    conn.execute(
        insert(pregnancy_records_t).values(
            id=pregnancy1_id,
            user_id=nkatha_id,
            last_menstrual_period=lmp1,
            due_date=due1,
            is_first_pregnancy=True,
            status="ENDED",
            outcome="LIVE_BIRTH",
            ended_at=ended_at,
            created_at=_dt(2024, 8, 15, 9, 0),
            updated_at=ended_at,
        )
    )

    vitals1 = [
        (date(2024, 9, 15), 112, 72, 62.0, ["NAUSEA"]),
        (date(2024, 11, 10), 110, 70, 65.5, []),
        (date(2025, 1, 5), 114, 74, 69.0, []),
        (date(2025, 2, 20), 116, 76, 71.5, ["BACK_PAIN"]),
        (date(2025, 4, 10), 118, 78, 73.5, []),
        (date(2025, 5, 1), 116, 74, 74.8, ["SWELLING"]),
    ]
    _seed_pregnancy_vitals(conn, nkatha_id, pregnancy1_id, preg_vitals_tmpl, vitals1, flagged_index=None)

    _seed_anc_visits(conn, pregnancy1_id, facility_id, lmp1, force_all_completed=True)

    # ----------------------------------------------------------------- #
    # 4.2 Cycle tracking — Phase B (postpartum resumption)                #
    # ----------------------------------------------------------------- #
    cycle_b = [
        {"ref": "cycleB1", "start": date(2025, 9, 10), "flow": "LIGHT", "clot": "NONE", "flags": []},
        {"ref": "cycleB2", "start": date(2025, 10, 12), "flow": "MODERATE", "clot": "NONE", "flags": []},
        {"ref": "cycleB3", "start": date(2025, 11, 8), "flow": "MODERATE", "clot": "NONE", "flags": []},
        {"ref": "cycleB4", "start": date(2025, 12, 6), "flow": "MODERATE", "clot": "SMALL", "flags": []},
        {"ref": "cycleB5", "start": date(2026, 1, 4), "flow": "MODERATE", "clot": "NONE", "flags": []},
    ]
    cycle_b_entry_ids = _seed_cycle_entries(conn, nkatha_id, cycle_entry_tmpl, cycle_b)

    _seed_pbac_items(conn, cycle_b_entry_ids["cycleB3"], [
        (date(2025, 11, 8), "MODERATELY_SOAKED", 5),
        (date(2025, 11, 9), "LIGHTLY_SOAKED", 1),
    ])

    symptoms_b = [
        (date(2025, 9, 10), ["FATIGUE"], "First period since Zawadi was born"),
        (date(2025, 10, 10), ["MOOD_SWINGS"], None),
        (date(2025, 11, 8), ["CRAMPS"], None),
        (date(2025, 12, 4), ["BLOATING", "HEADACHE"], None),
        (date(2026, 1, 4), ["CRAMPS", "FATIGUE"], None),
        (date(2026, 1, 29), ["NAUSEA"], "Missed period, feeling nauseous"),
    ]
    _seed_symptoms(conn, nkatha_id, cycle_symptom_tmpl, symptoms_b)

    # ----------------------------------------------------------------- #
    # 6. Postpartum & Baby Tracker — Baby #1 (Zawadi Nkatha)              #
    # ----------------------------------------------------------------- #
    baby1_id = uuid.uuid4()
    baby_dob = date(2025, 5, 14)

    conn.execute(
        insert(baby_profiles_t).values(
            id=baby1_id,
            user_id=nkatha_id,
            pregnancy_id=pregnancy1_id,
            name="Zawadi Nkatha",
            date_of_birth=baby_dob,
            time_of_birth=time(11, 20),
            gender="FEMALE",
            delivery_type="VAGINAL",
            birth_weight_kg=3.4,
            birth_length_cm=50.0,
            place_of_birth=FACILITY_NAME,
            notes="Healthy, breastfeeding well",
            created_at=ended_at,
            updated_at=ended_at,
        )
    )

    _seed_vaccination_schedule(conn, baby1_id, baby_dob, facility_id)
    _seed_postnatal_visits(conn, pregnancy1_id, ended_at.date(), facility_id)

    baby_vitals = [
        (date(2025, 5, 15), 36.9, 3.3, "BREASTFEEDING", 8, None),
        (date(2025, 6, 25), 36.7, 4.8, "BREASTFEEDING", 8, None),
        (date(2025, 8, 14), 36.8, 6.2, "BREASTFEEDING", 7, None),
        (date(2025, 11, 14), 36.6, 7.8, "BOTH", 6, "Started mixed feeding with formula top-ups"),
        (date(2026, 2, 14), 36.9, 8.6, "BOTH", 6, None),
        (date(2026, 5, 14), 36.8, 9.5, "BOTH", 5, "Now eating mashed solids alongside breastfeeding"),
        (date(2026, 7, 10), 36.7, 10.1, "BOTH", 5, "Eating three solid meals a day, breastfeeding morning and evening"),
    ]
    _seed_baby_vitals(conn, nkatha_id, baby1_id, baby_vitals_tmpl, baby_vitals)

    milestones = [
        ("MOVEMENT", "Held head up", date(2025, 6, 20)),
        ("FIRST_MOMENTS", "First social smile", date(2025, 6, 10)),
        ("GROWTH", "Tracks objects with eyes", date(2025, 6, 5)),
        ("GROWTH", "Coos and gurgles", date(2025, 7, 1)),
        ("MOVEMENT", "Rolled over", date(2025, 8, 20)),
        ("FIRST_MOMENTS", "Laughs out loud", date(2025, 8, 5)),
        ("GROWTH", "Babbles \"mama\"/\"baba\" sounds", date(2025, 10, 15)),
        ("MOVEMENT", "Sat without support", date(2025, 11, 20)),
        ("FIRST_MOMENTS", "Shows stranger anxiety, clings to mum", date(2025, 11, 10)),
        ("GROWTH", "Object permanence — looks for hidden toy", date(2025, 11, 25)),
        ("MOVEMENT", "Crawling", date(2026, 2, 14)),
        ("FIRST_MOMENTS", "Says first word — \"mama\"", date(2026, 2, 20)),
        ("FIRST_MOMENTS", "Waves bye-bye", date(2026, 3, 1)),
        ("GROWTH", "Points at objects of interest", date(2026, 3, 15)),
        ("MOVEMENT", "First steps", date(2026, 5, 20)),
        ("GROWTH", "Says 2–3 words", date(2026, 6, 1)),
        ("GROWTH", "Stacks two blocks", date(2026, 6, 20)),
    ]
    conn.execute(
        insert(baby_milestones_t),
        [
            {
                "id": uuid.uuid4(),
                "baby_id": baby1_id,
                "user_id": nkatha_id,
                "category": cat,
                "title": title,
                "achieved_at": achieved,
                "note": None,
                "photo_url": None,
                "created_at": _midnight(achieved),
            }
            for cat, title, achieved in milestones
        ],
    )

    maternal_checkins = [
        (date(2025, 5, 16), "HEAVY", 5, ["FATIGUE", "CRAMPING"]),
        (date(2025, 5, 21), "MODERATE", 3, ["FATIGUE"]),
        (date(2025, 5, 28), "LIGHT", 2, []),
        (date(2025, 6, 25), "NONE", 0, []),
    ]
    conn.execute(
        insert(form_submissions_t),
        [
            {
                "id": uuid.uuid4(),
                "template_id": maternal_checkin_tmpl,
                "user_id": nkatha_id,
                "context": "MATERNAL_CHECKIN",
                "answers": {"bleedingLevel": bleeding, "painLevel": pain, "symptoms": symptoms},
                "client_generated_id": None,
                "client_created_at": _midnight(d) + timedelta(hours=9),
                "created_at": _midnight(d) + timedelta(hours=9),
                "updated_at": _midnight(d) + timedelta(hours=9),
            }
            for d, bleeding, pain, symptoms in maternal_checkins
        ],
    )

    epds = [
        (date(2025, 5, 28), [1, 1, 0, 0, 0, 1, 0, 1, 0, 0]),
        (date(2025, 6, 25), [0, 1, 0, 0, 0, 0, 0, 1, 0, 0]),
    ]
    epds_rows = []
    for d, values in epds:
        total = sum(values)
        q10 = values[9]
        is_self_harm = q10 > 0
        if is_self_harm:
            level = "SELF_HARM_RISK"
        elif total >= 12:
            level = "HIGH"
        elif total >= 9:
            level = "MEDIUM"
        else:
            level = "LOW"
        epds_rows.append({
            "id": uuid.uuid4(),
            "user_id": nkatha_id,
            "answers": {f"q{i + 1}": v for i, v in enumerate(values)},
            "total_score": total,
            "q10_score": q10,
            "is_self_harm_flagged": is_self_harm,
            "risk_level": level,
            "created_at": _midnight(d) + timedelta(hours=10),
        })
    conn.execute(insert(epds_screenings_t), epds_rows)

    # ----------------------------------------------------------------- #
    # 5.2 Pregnancy #2 — current, active (week 24 as of 2026-07-21)      #
    # ----------------------------------------------------------------- #
    pregnancy2_id = uuid.uuid4()
    lmp2 = date(2026, 2, 2)
    due2 = lmp2 + timedelta(days=280)

    conn.execute(
        insert(pregnancy_records_t).values(
            id=pregnancy2_id,
            user_id=nkatha_id,
            last_menstrual_period=lmp2,
            due_date=due2,
            is_first_pregnancy=False,
            status="ACTIVE",
            outcome=None,
            ended_at=None,
            created_at=_dt(2026, 2, 3, 9, 0),
            updated_at=_dt(2026, 2, 3, 9, 0),
        )
    )

    vitals2 = [
        (date(2026, 2, 20), 110, 70, 60.0, ["FATIGUE"]),
        (date(2026, 3, 20), 112, 72, 61.5, []),
        (date(2026, 4, 17), 114, 74, 63.0, []),
        (date(2026, 5, 15), 128, 84, 65.5, ["SWELLING"]),
        (date(2026, 6, 12), 118, 76, 67.0, []),
        (date(2026, 7, 10), 116, 74, 68.5, []),
    ]
    _seed_pregnancy_vitals(conn, nkatha_id, pregnancy2_id, preg_vitals_tmpl, vitals2, flagged_index=3)

    _seed_anc_visits(conn, pregnancy2_id, facility_id, lmp2, force_all_completed=False)

    risk_history = [
        (date(2026, 2, 20), 0, "LOW", []),
        (date(2026, 3, 20), 0, "LOW", []),
        (date(2026, 4, 17), 0, "LOW", []),
        (date(2026, 5, 15), 35, "MEDIUM", [{
            "label": "Elevated blood pressure",
            "weight": 35,
            "severity": "WARNING",
            "description": "Blood pressure reading (128/84) exceeded the normal range at the week 15 visit",
        }]),
        (date(2026, 6, 12), 10, "LOW", [{
            "label": "Blood pressure within normal range",
            "weight": 0,
            "severity": "SUCCESS",
            "description": "Follow-up reading back within normal range",
        }]),
        (date(2026, 7, 10), 0, "LOW", []),
    ]
    conn.execute(
        insert(pregnancy_risk_scores_t),
        [
            {
                "id": uuid.uuid4(),
                "pregnancy_id": pregnancy2_id,
                "user_id": nkatha_id,
                "score": score,
                "level": level,
                "factors": factors,
                "clinician_override": None,
                "calculated_at": _midnight(d) + timedelta(hours=11),
            }
            for d, score, level, factors in risk_history
        ],
    )

    # ----------------------------------------------------------------- #
    # Education content + events (mobile Feed)                           #
    # ----------------------------------------------------------------- #
    _seed_education(conn, facility_id)

    print("Seeded Margret Nkatha demo dataset + education content.")


# --------------------------------------------------------------------------- #
# Section helpers                                                              #
# --------------------------------------------------------------------------- #

def _seed_cycle_entries(conn, user_id, template_id, entries: list[dict]) -> dict[str, uuid.UUID]:
    entry_ids: dict[str, uuid.UUID] = {}
    submission_rows = []
    entry_rows = []
    for e in entries:
        sub_id = uuid.uuid4()
        entry_id = uuid.uuid4()
        entry_ids[e["ref"]] = entry_id
        answers = {"flowLevel": e["flow"], "clotLevel": e["clot"], "flags": e["flags"]}
        score = 0
        flow_scores = {"LIGHT": 1, "MODERATE": 5, "HEAVY": 10, "VERY_HEAVY": 20}
        clot_scores = {"NONE": 0, "SMALL": 1, "LARGE": 5}
        score += flow_scores.get(e["flow"], 0)
        score += clot_scores.get(e["clot"], 0)
        created = _midnight(e["start"]) + timedelta(hours=8)
        submission_rows.append({
            "id": sub_id,
            "template_id": template_id,
            "user_id": user_id,
            "context": "CYCLE_ENTRY",
            "answers": answers,
            "client_generated_id": None,
            "client_created_at": created,
            "created_at": created,
            "updated_at": created,
        })
        entry_rows.append({
            "id": entry_id,
            "user_id": user_id,
            "submission_id": sub_id,
            "start_date": e["start"],
            "end_date": None,
            "pbac_score": score,
            "created_at": created,
            "updated_at": created,
        })
    conn.execute(insert(form_submissions_t), submission_rows)
    conn.execute(insert(cycle_entries_t), entry_rows)
    return entry_ids


def _seed_pbac_items(conn, cycle_entry_id, items: list[tuple]) -> None:
    conn.execute(
        insert(pbac_items_t),
        [
            {
                "id": uuid.uuid4(),
                "cycle_entry_id": cycle_entry_id,
                "date": d,
                "item_type": "PAD",
                "soak_level": soak,
                "point_value": points,
                "created_at": _midnight(d) + timedelta(hours=20),
            }
            for d, soak, points in items
        ],
    )


def _seed_symptoms(conn, user_id, template_id, symptoms: list[tuple]) -> None:
    rows = []
    for d, symptom_list, notes in symptoms:
        created = datetime(d.year, d.month, d.day, tzinfo=UTC)
        rows.append({
            "id": uuid.uuid4(),
            "template_id": template_id,
            "user_id": user_id,
            "context": "CYCLE_SYMPTOM",
            "answers": {"symptoms": symptom_list, "notes": notes},
            "client_generated_id": None,
            "client_created_at": created,
            "created_at": created,
            "updated_at": created,
        })
    conn.execute(insert(form_submissions_t), rows)


def _seed_pregnancy_vitals(conn, user_id, pregnancy_id, template_id, vitals: list[tuple], flagged_index) -> None:
    submission_rows = []
    entry_rows = []
    for i, (d, sbp, dbp, weight, symptoms) in enumerate(vitals):
        sub_id = uuid.uuid4()
        created = _midnight(d) + timedelta(hours=9)
        submission_rows.append({
            "id": sub_id,
            "template_id": template_id,
            "user_id": user_id,
            "context": "PREGNANCY_VITALS",
            "answers": {"systolicBp": sbp, "diastolicBp": dbp, "weightKg": weight, "symptoms": symptoms},
            "client_generated_id": None,
            "client_created_at": created,
            "created_at": created,
            "updated_at": created,
        })
        is_flagged = flagged_index is not None and i == flagged_index
        entry_rows.append({
            "id": uuid.uuid4(),
            "pregnancy_id": pregnancy_id,
            "submission_id": sub_id,
            "is_flagged": is_flagged,
            "flagged_reasons": (
                [f"HIGH_BLOOD_PRESSURE: elevated reading ({sbp}/{dbp}) at the week visit"] if is_flagged else []
            ),
            "created_at": created,
            "updated_at": created,
        })
    conn.execute(insert(form_submissions_t), submission_rows)
    conn.execute(insert(pregnancy_vitals_entries_t), entry_rows)


def _seed_anc_visits(conn, pregnancy_id, facility_id, lmp: date, force_all_completed: bool) -> None:
    milestones = _get_pathway_milestones(conn, "path_anc_moh_v1")
    today = datetime.now(UTC)
    rows = []
    for m in milestones:
        scheduled_date = lmp + timedelta(weeks=m.get("triggerWeek", 0))
        scheduled_at = _midnight(scheduled_date)
        is_past = force_all_completed or scheduled_at < today
        rows.append({
            "id": uuid.uuid4(),
            "pregnancy_id": pregnancy_id,
            "baby_id": None,
            "pathway_template_id": "path_anc_moh_v1",
            "milestone_order": m.get("order"),
            "label": m.get("label", "ANC visit"),
            "scheduled_at": scheduled_at,
            "status": "COMPLETED" if is_past else "SCHEDULED",
            "facility_id": facility_id,
            "purpose": None,
            "summary": "All normal, baby growing well" if is_past else None,
            "created_at": scheduled_at,
            "updated_at": scheduled_at,
        })
    if rows:
        conn.execute(insert(scheduled_visits_t), rows)


def _seed_postnatal_visits(conn, pregnancy_id, delivery_date: date, facility_id) -> None:
    milestones = _get_pathway_milestones(conn, "path_postnatal_moh_v1")
    rows = []
    for m in milestones:
        scheduled_date = delivery_date + timedelta(days=m.get("triggerDays", 0))
        scheduled_at = _midnight(scheduled_date)
        covers = m.get("covers", ["MOTHER", "BABY"])
        rows.append({
            "id": uuid.uuid4(),
            "pregnancy_id": pregnancy_id,
            "baby_id": None,
            "pathway_template_id": "path_postnatal_moh_v1",
            "milestone_order": m.get("order"),
            "label": m.get("label", "Postnatal visit"),
            "scheduled_at": scheduled_at,
            "status": "COMPLETED",
            "facility_id": facility_id,
            "purpose": ",".join(covers) if isinstance(covers, list) else str(covers),
            "summary": "Mother and baby both doing well",
            "created_at": scheduled_at,
            "updated_at": scheduled_at,
        })
    if rows:
        conn.execute(insert(scheduled_visits_t), rows)


def _seed_vaccination_schedule(conn, baby_id, dob: date, facility_id) -> None:
    milestones = _get_pathway_milestones(conn, "path_vaccination_moh_v1")

    given_at_by_week = {
        0: _dt(2025, 5, 14, 11, 30),
        6: _dt(2025, 6, 25, 9, 0),
        10: _dt(2025, 7, 23, 9, 15),
        14: _dt(2025, 8, 20, 9, 10),
        39: _dt(2026, 2, 14, 10, 0),
    }
    batch_by_week = {
        0: "BCG-2025-0442",
        6: "PENTA1-2025-1187",
        10: "PENTA2-2025-1390",
        14: "PENTA3-2025-1602",
        39: "MR1-2026-0298",
    }
    UPCOMING_VACCINE_ID = "vac_mr2"  # 18-month booster — left unmarked so one row shows as upcoming

    visit_rows = []
    visit_ids_by_vaccine = {}
    for m in milestones:
        visit_id = uuid.uuid4()
        trigger_week = m.get("triggerWeek", 0)
        scheduled_date = dob + timedelta(weeks=trigger_week)
        scheduled_at = _midnight(scheduled_date)
        vaccine_id = m.get("vaccineId")
        is_given = vaccine_id != UPCOMING_VACCINE_ID and trigger_week in given_at_by_week
        visit_ids_by_vaccine[vaccine_id] = visit_id
        visit_rows.append({
            "id": visit_id,
            "pregnancy_id": None,
            "baby_id": baby_id,
            "pathway_template_id": "path_vaccination_moh_v1",
            "milestone_order": m.get("order"),
            "label": m.get("label", "Vaccination"),
            "scheduled_at": scheduled_at,
            "status": "COMPLETED" if is_given else "SCHEDULED",
            "facility_id": facility_id,
            "purpose": vaccine_id,
            "summary": None,
            "created_at": scheduled_at,
            "updated_at": scheduled_at,
        })
    if visit_rows:
        conn.execute(insert(scheduled_visits_t), visit_rows)

    record_rows = []
    for m in milestones:
        vaccine_id = m.get("vaccineId")
        trigger_week = m.get("triggerWeek", 0)
        if vaccine_id == UPCOMING_VACCINE_ID or trigger_week not in given_at_by_week:
            continue
        record_rows.append({
            "id": uuid.uuid4(),
            "baby_id": baby_id,
            "scheduled_visit_id": visit_ids_by_vaccine[vaccine_id],
            "vaccine_id": vaccine_id,
            "given_at": given_at_by_week[trigger_week],
            "facility_id": str(facility_id),
            "batch_number": batch_by_week[trigger_week],
            "created_at": given_at_by_week[trigger_week],
        })
    if record_rows:
        conn.execute(insert(baby_vaccination_records_t), record_rows)


def _seed_baby_vitals(conn, user_id, baby_id, template_id, vitals: list[tuple]) -> None:
    rows = []
    for d, temp, weight, feeding, feed_count, notes in vitals:
        created = _midnight(d) + timedelta(hours=8)
        answers = {
            "temperatureCelsius": temp,
            "weightKg": weight,
            "feedingType": feeding,
            "feedCountToday": feed_count,
            "symptoms": ["ALL_NORMAL"],
        }
        if notes:
            answers["notes"] = notes
        rows.append({
            "id": uuid.uuid4(),
            "template_id": template_id,
            "user_id": user_id,
            "context": "BABY_VITALS",
            "answers": {**answers, "baby_id": str(baby_id)},
            "client_generated_id": None,
            "client_created_at": created,
            "created_at": created,
            "updated_at": created,
        })
    conn.execute(insert(form_submissions_t), rows)


def _seed_education(conn, facility_id) -> None:
    articles = [
        ("HYDRATION", "Why hydration matters more during pregnancy",
         "Blood volume rises by up to 50% in pregnancy, and water supports amniotic fluid levels, digestion and "
         "nutrient transport to your baby. Aim for 8-10 glasses a day, more if you're active or it's hot.",
         ["PREGNANT"]),
        ("HYDRATION", "Staying hydrated while breastfeeding",
         "Breastfeeding increases your fluid needs — keep a water bottle within reach at every feed. Herbal teas "
         "and soups count too, but limit caffeinated drinks.",
         ["POSTPARTUM"]),
        ("HYDRATION", "Spotting the signs of dehydration early",
         "Dark urine, headaches, dizziness and reduced baby movement can all signal dehydration. Increase fluids "
         "immediately and contact your clinic if symptoms persist.",
         ["PREGNANT", "POSTPARTUM"]),
        ("HYDRATION", "Simple ways to drink more water every day",
         "Carry a bottle everywhere, flavour water with lemon or mint if plain water feels unappealing, and set "
         "reminders on your phone until it becomes a habit.",
         ["PREGNANT", "POSTPARTUM", "NOT_PREGNANT"]),

        ("NUTRITION", "Iron-rich foods for a healthy pregnancy",
         "Dark leafy greens, legumes, lean red meat and fortified cereals help prevent anaemia. Pair with vitamin "
         "C-rich foods like oranges or tomatoes to boost absorption.",
         ["PREGNANT"]),
        ("NUTRITION", "Eating well while breastfeeding",
         "You need roughly 450-500 extra calories a day while breastfeeding. Focus on whole grains, protein and "
         "healthy fats rather than empty calories.",
         ["POSTPARTUM"]),
        ("NUTRITION", "Folic acid: what it does and why it matters early on",
         "Folic acid helps prevent neural tube defects in the first weeks of pregnancy, often before you know "
         "you're pregnant. A daily 400mcg supplement is recommended if you're trying to conceive.",
         ["PREGNANT", "NOT_PREGNANT"]),
        ("NUTRITION", "Balanced meals on a budget for new mothers",
         "Beans, eggs, seasonal vegetables and whole grains give you balanced nutrition without straining your "
         "budget. Batch-cooking on good days saves energy on harder ones.",
         ["POSTPARTUM", "NOT_PREGNANT"]),

        ("EXERCISE", "Safe exercises for each trimester",
         "Walking, swimming and prenatal yoga are generally safe throughout pregnancy. Avoid contact sports, "
         "activities with a fall risk, and lying flat on your back after the first trimester.",
         ["PREGNANT"]),
        ("EXERCISE", "Gentle postpartum recovery movement",
         "Start with short walks and gentle stretching once cleared by your clinician, usually after your 6-week "
         "check. Listen to your body and build up gradually.",
         ["POSTPARTUM"]),
        ("EXERCISE", "Pelvic floor exercises every mother should know",
         "Kegel exercises strengthen the muscles supporting your bladder, uterus and bowel. Practice them daily, "
         "during and after pregnancy, to reduce leakage and support recovery.",
         ["PREGNANT", "POSTPARTUM"]),
        ("EXERCISE", "Walking your way back to fitness after birth",
         "Walking is low-impact, requires no equipment, and can be done with baby in a sling or pram. Start with "
         "10-15 minutes and build up as your energy returns.",
         ["POSTPARTUM"]),

        ("MENTAL_HEALTH", "Coping with anxiety during pregnancy",
         "It's common to feel anxious about labour, your baby's health, or the changes ahead. Talking to your "
         "partner, midwife or a counsellor can help you process these feelings.",
         ["PREGNANT"]),
        ("MENTAL_HEALTH", "Understanding the baby blues vs postpartum depression",
         "The baby blues usually pass within two weeks of delivery. If low mood, hopelessness or loss of interest "
         "persist longer, or feel severe, reach out to your clinician — support is available.",
         ["POSTPARTUM"]),
        ("MENTAL_HEALTH", "Building a support system before your baby arrives",
         "Identify family, friends or community groups who can help with meals, errands or simply listening in "
         "the early weeks after birth. Asking for help early makes a real difference.",
         ["PREGNANT"]),
        ("MENTAL_HEALTH", "Talking to your partner about mental health after birth",
         "Open, regular check-ins with your partner about how you're both coping can catch struggles early. "
         "Mental health screenings like the EPDS are a normal, useful part of postnatal care.",
         ["POSTPARTUM"]),

        ("GENERAL", "What to pack in your hospital bag",
         "Pack ID and antenatal records, comfortable clothing, toiletries, baby's first outfit and going-home "
         "clothes, and phone chargers. Prepare this bag by week 36.",
         ["PREGNANT"]),
        ("GENERAL", "Understanding your antenatal care schedule",
         "The standard MOH schedule includes 8 contacts across your pregnancy for blood pressure, weight, fetal "
         "growth and screening checks. Keeping every visit helps catch issues early.",
         ["PREGNANT"]),
        ("GENERAL", "Recognising danger signs — when to seek help immediately",
         "Heavy bleeding, severe headaches, blurred vision, reduced baby movement, high fever or severe abdominal "
         "pain need urgent attention — contact your facility or emergency services right away.",
         ["PREGNANT", "POSTPARTUM"]),
        ("GENERAL", "Family planning options after delivery",
         "Discuss spacing and contraception options with your clinician at your 6-week check — options range "
         "from lactation amenorrhea to long-acting reversible methods.",
         ["POSTPARTUM", "NOT_PREGNANT"]),
    ]

    conn.execute(
        insert(education_content_t),
        [
            {
                "id": uuid.uuid4(),
                "title": title,
                "category": category,
                "body": body,
                "target_stages": stages,
                "facility_id": facility_id,
                "created_at": datetime.now(UTC) - timedelta(days=idx),
                "updated_at": datetime.now(UTC) - timedelta(days=idx),
            }
            for idx, (category, title, body, stages) in enumerate(articles)
        ],
    )

    events = [
        ("Free Antenatal Education Class", _dt(2026, 8, 5, 9, 0),
         "A free class covering labour preparation, breastfeeding basics and newborn care, open to all expectant mothers."),
        ("Breastfeeding Support Group Meetup", _dt(2026, 7, 30, 14, 0),
         "A peer support session for breastfeeding mothers, facilitated by our lactation team. Bring your baby along."),
        ("Community Immunization Outreach Day", _dt(2026, 8, 12, 8, 30),
         "Free infant immunizations and growth monitoring for children under 5, no appointment required."),
        ("Postpartum Wellness & Family Planning Clinic", _dt(2026, 8, 20, 10, 0),
         "Postnatal checkups, EPDS screening and family planning counselling for mothers within their first year after delivery."),
    ]
    conn.execute(
        insert(education_events_t),
        [
            {
                "id": uuid.uuid4(),
                "title": title,
                "facility_id": facility_id,
                "event_date": event_date,
                "description": description,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
            for title, event_date, description in events
        ],
    )


def downgrade() -> None:
    conn = op.get_bind()

    nkatha_row = conn.execute(select(users_t.c.id).where(users_t.c.phone_number == NKATHA_PHONE)).fetchone()
    clinician_row = conn.execute(select(users_t.c.id).where(users_t.c.phone_number == CLINICIAN_PHONE)).fetchone()
    facility_row = conn.execute(
        select(facilities_t.c.id).where(
            facilities_t.c.name == FACILITY_NAME, facilities_t.c.county == FACILITY_COUNTY
        )
    ).fetchone()

    if nkatha_row:
        nkatha_id = nkatha_row[0]
        conn.execute(sa.text("DELETE FROM baby_profiles WHERE user_id = :uid"), {"uid": nkatha_id})
        conn.execute(sa.text("DELETE FROM pregnancy_records WHERE user_id = :uid"), {"uid": nkatha_id})
        conn.execute(sa.text("DELETE FROM epds_screenings WHERE user_id = :uid"), {"uid": nkatha_id})
        conn.execute(sa.text("DELETE FROM medical_history_records WHERE patient_user_id = :uid"), {"uid": nkatha_id})
        conn.execute(sa.text("DELETE FROM form_submissions WHERE user_id = :uid"), {"uid": nkatha_id})
        conn.execute(sa.text("DELETE FROM users WHERE id = :uid"), {"uid": nkatha_id})

    if facility_row:
        facility_id = facility_row[0]
        conn.execute(sa.text("DELETE FROM education_content WHERE facility_id = :fid"), {"fid": facility_id})
        conn.execute(sa.text("DELETE FROM education_events WHERE facility_id = :fid"), {"fid": facility_id})

    if clinician_row:
        clinician_id = clinician_row[0]
        conn.execute(sa.text("DELETE FROM staff_members WHERE user_id = :uid"), {"uid": clinician_id})
        conn.execute(
            sa.text("DELETE FROM medical_history_records WHERE created_by = :uid OR last_updated_by = :uid"),
            {"uid": clinician_id},
        )
        conn.execute(sa.text("DELETE FROM users WHERE id = :uid"), {"uid": clinician_id})

    # Only remove the demo templates we may have created, and only once nothing
    # references them any more (leaves any pre-existing, reused template alone).
    for slug in ("tmpl_cycle_entry_v1", "tmpl_symptom_entry_v1", "tmpl_preg_vitals_v1", "tmpl_postpartum_checkin_v1"):
        conn.execute(
            sa.text(
                "DELETE FROM form_templates "
                "WHERE slug = :slug "
                "AND NOT EXISTS (SELECT 1 FROM form_submissions WHERE form_submissions.template_id = form_templates.id)"
            ),
            {"slug": slug},
        )

    if facility_row:
        facility_id = facility_row[0]
        conn.execute(
            sa.text(
                "DELETE FROM facilities WHERE id = :fid "
                "AND NOT EXISTS (SELECT 1 FROM staff_members WHERE staff_members.facility_id = facilities.id) "
                "AND NOT EXISTS (SELECT 1 FROM profiles WHERE profiles.preferred_facility_id = facilities.id) "
                "AND NOT EXISTS (SELECT 1 FROM education_content WHERE education_content.facility_id = facilities.id) "
                "AND NOT EXISTS (SELECT 1 FROM education_events WHERE education_events.facility_id = facilities.id)"
            ),
            {"fid": facility_id},
        )
