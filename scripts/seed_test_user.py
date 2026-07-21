"""
Seed script: full-journey test patient — now tracking menstrual cycle
  Story: Meru Nkatha had her first pregnancy, delivered, completed postpartum,
         and has now returned to regular cycle tracking. She is NOT pregnant.

  1. User + Profile (stage = NOT_PREGNANT)
  2. ENDED Pregnancy → risk scores + antenatal visits + vitals entries
  3. Closed Labour session → readings + alert
  4. Postpartum → BabyProfile + milestones + vaccinations + EPDS screening
  5. Medical history record
  6. Menstrual cycle entries (3 completed cycles + 1 current) with PBAC items

Run from the project root:
    python -m scripts.seed_test_user
"""

import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone, time

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models import (
    User, UserRole, Profile,
    PregnancyRecord, PregnancyStatus, PregnancyOutcome,
    PregnancyVitalsEntry, PregnancyRiskScore, RiskLevel,
    ScheduledVisit, VisitStatus,
    LabourSession, LabourSessionStatus, LabourOutcome, LabourDeliveryType,
    LabourReading, LabourReadingType,
    LabourAlert, AlertType, AlertSeverity,
    BabyProfile, BabyGender, EpdsScreening, EpdsRiskLevel,
    MedicalHistoryRecord,
    FormTemplate, FormSubmission, FormContext,
    CycleEntry, PbacItem, PbacItemType, PbacSoakLevel,
)
# Items not re-exported from app.models.__init__ — import directly from submodules
from app.models.postpartum import (
    DeliveryType, BabyMilestone, MilestoneCategory, BabyVaccinationRecord,
)
from app.models.profile import (
    CurrentStage, SharingPreference, NotificationPreference, CompanionPreference,
)

# ─────────────────────── constants ───────────────────────────────────────────

TEST_PHONE  = "+254700000001"
TEST_NAME   = "Meru Nkatha"
TEST_COUNTY = "Meru"
TODAY       = date.today()
NOW_UTC     = datetime.now(timezone.utc)

# ── Timeline ────────────────────────────────────────────────────────────────
# Pregnancy: LMP ~13 months ago → baby born ~9 months ago
# Postpartum ended: ~6 weeks after birth (~7.5 months ago)
# Cycle tracking resumed: ~7 months ago (3 full cycles + 1 ongoing)

LMP        = TODAY - timedelta(days=396)          # ~13 months ago
DUE_DATE   = LMP + timedelta(weeks=40)            # ~9.7 months ago
BIRTH_DATE = DUE_DATE + timedelta(days=3)         # slightly past due
POSTPARTUM_END = BIRTH_DATE + timedelta(weeks=6)  # 6-week postnatal period ends

# First menstrual cycle resumed ~2 weeks after postpartum end
CYCLE1_START = POSTPARTUM_END + timedelta(weeks=2)
CYCLE2_START = CYCLE1_START + timedelta(days=29)
CYCLE3_START = CYCLE2_START + timedelta(days=27)  # current period — started 2 days ago, still ongoing

# Facility and clinician will be assigned later via the normal app flow


# ─────────────────────── helpers ─────────────────────────────────────────────

def dt(d: date, hour: int = 8) -> datetime:
    """Return a UTC-aware datetime for a given date and hour."""
    return datetime(d.year, d.month, d.day, hour, 0, 0, tzinfo=timezone.utc)


# ─────────────────────── cleanup ─────────────────────────────────────────────

async def delete_existing(session: AsyncSession) -> None:
    result = await session.execute(select(User).where(User.phone_number == TEST_PHONE))
    existing = result.scalar_one_or_none()
    if existing:
        print(f"  ↳ Found existing user {existing.id}. Deleting all their data…")
        # medical_history_records.created_by / last_updated_by have no ON DELETE CASCADE,
        # so we must delete the medical history row manually first.
        await session.execute(
            delete(MedicalHistoryRecord).where(MedicalHistoryRecord.patient_user_id == existing.id)
        )
        await session.flush()
        await session.delete(existing)
        await session.flush()
        print("  ↳ Existing user deleted.")


# ─────────────────────── seeding ─────────────────────────────────────────────

async def seed() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():

            # ── 0. Clean up ───────────────────────────────────────────────
            print("\n[1/9] Cleaning up existing test data…")
            await delete_existing(session)

            # ── 1. User ───────────────────────────────────────────────────
            print("[2/9] Creating User…")
            user = User(
                id=uuid.uuid4(),
                phone_number=TEST_PHONE,
                password_hash=get_password_hash("Test1234!"),  # simple test password
                role=UserRole.USER,
                full_name=TEST_NAME,
                date_of_birth=date(1995, 4, 12),
                preferred_language="en",
                county=TEST_COUNTY,
                is_active=True,
            )
            session.add(user)
            await session.flush()

            # ── 2. Profile ────────────────────────────────────────────────
            print("[3/9] Creating Profile…")
            profile = Profile(
                id=uuid.uuid4(),
                user_id=user.id,
                current_stage=CurrentStage.NOT_PREGNANT,   # back to regular tracking
                emergency_sharing_preference=SharingPreference.ALWAYS_SHARE,
                notification_preference=NotificationPreference.BOTH,
                companion_preference=CompanionPreference.AI_DOC,
                emergency_contact_name="James Mugambi",
                emergency_contact_relationship="Spouse",
                emergency_contact_phone="+254711000002",
                home_address_name="Meru Town, Meru County",
                home_location_lat="-0.0467",
                home_location_lng="37.6490",
                typical_cycle_length_days=28,
            )
            session.add(profile)

            # ── 3. Pregnancy record (ENDED → live birth) ──────────────────
            print("[4/9] Creating Pregnancy record…")
            pregnancy = PregnancyRecord(
                id=uuid.uuid4(),
                user_id=user.id,
                last_menstrual_period=LMP,
                due_date=DUE_DATE,
                is_first_pregnancy=True,
                status=PregnancyStatus.ENDED,
                outcome=PregnancyOutcome.LIVE_BIRTH,
                ended_at=dt(BIRTH_DATE, 14),
            )
            session.add(pregnancy)
            await session.flush()

            # Risk scores over the pregnancy
            for score_val, level, weeks_ago, factors in [
                (5,  RiskLevel.LOW,    36, ["No complications noted"]),
                (22, RiskLevel.MEDIUM, 20, ["Elevated BP at week 28", "Mild oedema"]),
                (10, RiskLevel.LOW,    10, ["BP normalised", "Good fetal movement"]),
            ]:
                session.add(PregnancyRiskScore(
                    id=uuid.uuid4(),
                    pregnancy_id=pregnancy.id,
                    user_id=user.id,
                    score=score_val,
                    level=level,
                    factors=factors,
                    calculated_at=NOW_UTC - timedelta(weeks=weeks_ago),
                ))

            # Antenatal + postnatal scheduled visits
            visit_data = [
                ("1st Antenatal Visit", 8,  VisitStatus.COMPLETED, "Booking visit"),
                ("2nd Antenatal Visit", 16, VisitStatus.COMPLETED, "Anomaly scan"),
                ("3rd Antenatal Visit", 24, VisitStatus.COMPLETED, "Glucose tolerance test"),
                ("4th Antenatal Visit", 28, VisitStatus.COMPLETED, "BP check + iron supplements"),
                ("5th Antenatal Visit", 32, VisitStatus.COMPLETED, "Growth scan"),
                ("6th Antenatal Visit", 36, VisitStatus.MISSED,    "Cervix check"),
                ("7th Antenatal Visit", 38, VisitStatus.COMPLETED, "Birth plan discussion"),
                ("6-Week Postnatal Check", 46, VisitStatus.COMPLETED, "Postnatal review"),
            ]
            for label, weeks_from_lmp, status, purpose in visit_data:
                visit_date = LMP + timedelta(weeks=weeks_from_lmp)
                session.add(ScheduledVisit(
                    id=uuid.uuid4(),
                    pregnancy_id=pregnancy.id,
                    label=label,
                    scheduled_at=dt(visit_date, 9),
                    status=status,
                    facility_id=None,   # to be set when linked to a real facility
                    purpose=purpose,
                    summary="Visit completed without issues." if status == VisitStatus.COMPLETED else None,
                ))

            # Pregnancy vitals entries
            print("[5/9] Creating Pregnancy vitals entries…")
            vitals_template = FormTemplate(
                id=uuid.uuid4(),
                slug="pregnancy-vitals-seed-v1",
                context=FormContext.PREGNANCY_VITALS,
                fields={
                    "blood_pressure_systolic":  {"type": "number", "label": "BP Systolic (mmHg)"},
                    "blood_pressure_diastolic": {"type": "number", "label": "BP Diastolic (mmHg)"},
                    "weight_kg":                {"type": "number", "label": "Weight (kg)"},
                    "fetal_movements":          {"type": "single_select", "label": "Fetal Movements",
                                                 "options": ["normal", "reduced", "increased"]},
                    "symptoms":                 {"type": "multi_select", "label": "Symptoms",
                                                 "options": ["headache", "swelling", "nausea", "none"]},
                },
                version="v1",
                is_active=False,    # seed-only template, not active
                facility_id=None,
            )
            session.add(vitals_template)
            await session.flush()

            for week, sys_bp, dia_bp, wt, movements, symptoms, flagged, reasons in [
                (10, 112, 72, 58.0,  "normal",   ["none"],                  False, []),
                (14, 115, 74, 60.2,  "normal",   ["nausea"],                False, []),
                (18, 118, 76, 62.5,  "normal",   ["none"],                  False, []),
                (22, 120, 78, 65.0,  "normal",   ["none"],                  False, []),
                (26, 128, 82, 67.3,  "normal",   ["headache"],              False, []),
                (28, 140, 90, 69.1,  "normal",   ["headache", "swelling"],  True,  ["Elevated BP ≥140/90"]),
                (30, 132, 84, 70.5,  "normal",   ["swelling"],              True,  ["Persistent oedema"]),
                (32, 125, 80, 71.8,  "normal",   ["none"],                  False, []),
                (34, 120, 76, 73.0,  "normal",   ["none"],                  False, []),
                (36, 118, 75, 74.5,  "normal",   ["none"],                  False, []),
                (38, 116, 74, 75.2,  "increased",["none"],                  False, []),
            ]:
                sub = FormSubmission(
                    id=uuid.uuid4(),
                    template_id=vitals_template.id,
                    user_id=user.id,
                    context=FormContext.PREGNANCY_VITALS,
                    answers={
                        "blood_pressure_systolic":  sys_bp,
                        "blood_pressure_diastolic": dia_bp,
                        "weight_kg":                wt,
                        "fetal_movements":          movements,
                        "symptoms":                 symptoms,
                    },
                    client_created_at=dt(LMP + timedelta(weeks=week), 10),
                )
                session.add(sub)
                await session.flush()
                session.add(PregnancyVitalsEntry(
                    id=uuid.uuid4(),
                    pregnancy_id=pregnancy.id,
                    submission_id=sub.id,
                    is_flagged=flagged,
                    flagged_reasons=reasons,
                ))

            # ── 4. Labour session (closed) ────────────────────────────────
            print("[6/9] Creating Labour session…")
            labour_start = dt(BIRTH_DATE, 4)
            labour = LabourSession(
                id=uuid.uuid4(),
                pregnancy_id=pregnancy.id,
                facility_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),   # placeholder
                clinician_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # placeholder
                active_labour_started_at=labour_start,
                status=LabourSessionStatus.CLOSED,
                outcome=LabourOutcome.LIVE_BIRTH,
                delivery_type=LabourDeliveryType.VAGINAL,
                closed_at=dt(BIRTH_DATE, 14),
                room="LW-3",
            )
            session.add(labour)
            await session.flush()

            for h_offset, r_type, r_value, r_meta in [
                (0, LabourReadingType.DILATION,     3,   None),
                (0, LabourReadingType.FHR,          145, None),
                (0, LabourReadingType.MATERNAL_BP,  None, {"systolic": 128, "diastolic": 84}),
                (2, LabourReadingType.DILATION,     5,   None),
                (2, LabourReadingType.FHR,          148, None),
                (2, LabourReadingType.CONTRACTIONS, None, {"duration_sec": 45, "frequency_per_10min": 3}),
                (4, LabourReadingType.DILATION,     7,   None),
                (4, LabourReadingType.FHR,          140, None),
                (4, LabourReadingType.MATERNAL_BP,  None, {"systolic": 132, "diastolic": 88}),
                (6, LabourReadingType.DILATION,     9,   None),
                (6, LabourReadingType.FHR,          135, None),
                (6, LabourReadingType.CONTRACTIONS, None, {"duration_sec": 60, "frequency_per_10min": 4}),
                (8, LabourReadingType.DILATION,     10,  None),
                (8, LabourReadingType.FHR,          142, None),
                (8, LabourReadingType.MATERNAL_BP,  None, {"systolic": 125, "diastolic": 82}),
            ]:
                session.add(LabourReading(
                    id=uuid.uuid4(),
                    session_id=labour.id,
                    type=r_type,
                    value=r_value,
                    meta=r_meta,
                    recorded_at=labour_start + timedelta(hours=h_offset),
                ))

            session.add(LabourAlert(
                id=uuid.uuid4(),
                session_id=labour.id,
                type=AlertType.PREECLAMPSIA_RISK,
                severity=AlertSeverity.WARNING,
                message="BP reading at 08:00 slightly elevated (132/88). Monitor closely.",
                acknowledged_at=labour_start + timedelta(hours=4, minutes=30),
                acknowledged_by=None,   # to be set when clinician is linked
            ))

            # ── 5. Baby Profile ───────────────────────────────────────────
            print("[7/9] Creating Baby Profile, milestones, vaccinations & EPDS…")
            baby = BabyProfile(
                id=uuid.uuid4(),
                user_id=user.id,
                pregnancy_id=pregnancy.id,
                name="Baby Nkatha",
                date_of_birth=BIRTH_DATE,
                time_of_birth=time(14, 22),
                gender=BabyGender.FEMALE,
                delivery_type=DeliveryType.VAGINAL,
                birth_weight_kg=3.2,
                birth_length_cm=50.0,
                place_of_birth="Meru Level 5 Hospital",
                notes="Healthy newborn, Apgar score 9/10.",
            )
            session.add(baby)
            await session.flush()

            for cat, title, achieved in [
                (MilestoneCategory.FIRST_MOMENTS, "First smile",          BIRTH_DATE + timedelta(weeks=6)),
                (MilestoneCategory.SLEEP,         "Sleeps 6h straight",   BIRTH_DATE + timedelta(weeks=12)),
                (MilestoneCategory.MOVEMENT,      "Rolled over",          BIRTH_DATE + timedelta(weeks=16)),
                (MilestoneCategory.GROWTH,        "Doubled birth weight", BIRTH_DATE + timedelta(weeks=18)),
                (MilestoneCategory.FEEDING,       "Started solids",       BIRTH_DATE + timedelta(weeks=24)),
            ]:
                if achieved <= TODAY:
                    session.add(BabyMilestone(
                        id=uuid.uuid4(),
                        baby_id=baby.id,
                        user_id=user.id,
                        category=cat,
                        title=title,
                        achieved_at=achieved,
                    ))

            for vaccine_id, offset_weeks in [
                ("vac_bcg",    0),
                ("vac_opv0",   0),
                ("vac_penta1", 6),
                ("vac_opv1",   6),
                ("vac_pcv1",   6),
            ]:
                given_date = BIRTH_DATE + timedelta(weeks=offset_weeks)
                if given_date <= TODAY:
                    session.add(BabyVaccinationRecord(
                        id=uuid.uuid4(),
                        baby_id=baby.id,
                        vaccine_id=vaccine_id,
                        given_at=dt(given_date, 10),
                        facility_id=None,
                        batch_number=f"BATCH-{vaccine_id.upper()}-2025",
                    ))

            epds_answers = {
                "q1": 0, "q2": 0, "q3": 1, "q4": 0,
                "q5": 1, "q6": 0, "q7": 0, "q8": 0,
                "q9": 0, "q10": 0,
            }
            session.add(EpdsScreening(
                id=uuid.uuid4(),
                user_id=user.id,
                answers=epds_answers,
                total_score=sum(epds_answers.values()),
                q10_score=epds_answers["q10"],
                is_self_harm_flagged=False,
                risk_level=EpdsRiskLevel.LOW,
                created_at=dt(BIRTH_DATE + timedelta(weeks=6), 11),
            ))

            # ── 6. Medical history ────────────────────────────────────────
            print("[8/9] Creating Medical History record…")
            session.add(MedicalHistoryRecord(
                id=uuid.uuid4(),
                patient_user_id=user.id,
                created_by=user.id,
                last_updated_by=user.id,

                # Blood profile
                blood_type="A",
                rh_factor="+",

                # Allergies
                allergies=["Penicillin", "Sulfonamides"],

                # Chronic conditions — gestational hypertension resolved post-delivery
                chronic_conditions=[
                    "Gestational hypertension (resolved post-delivery)",
                    "Iron-deficiency anaemia (managed during pregnancy)",
                ],

                # Current medications — iron supplement continuing post-delivery
                current_medications=[
                    {
                        "name": "Ferrous Sulfate",
                        "dose": "200mg",
                        "frequency": "Once daily",
                        "reason": "Iron-deficiency anaemia",
                        "since": str(BIRTH_DATE),
                    },
                    {
                        "name": "Folic Acid",
                        "dose": "5mg",
                        "frequency": "Once daily",
                        "reason": "Post-pregnancy supplementation",
                        "since": str(BIRTH_DATE),
                    },
                ],

                # Surgical history
                surgical_history=[
                    {
                        "procedure": "Appendectomy",
                        "year": 2015,
                        "hospital": "Meru Level 5 Hospital",
                        "notes": "Laparoscopic, uneventful recovery",
                    },
                ],

                # Obstetric history
                previous_pregnancies=1,
                previous_outcomes=["LIVE_BIRTH"],

                # Family history — both maternal and paternal
                family_history=[
                    "Hypertension — mother and maternal grandmother",
                    "Type 2 diabetes — maternal uncle",
                    "Breast cancer — maternal aunt (diagnosed at 55)",
                    "Sickle cell trait — father (carrier)",
                ],

                # Custom fields — additional clinical notes
                custom_fields={
                    "mental_health_notes": "Mild postpartum blues week 1-2; resolved by week 6. EPDS score 2/30.",
                    "dental_notes": "Last dental visit March 2025. No active caries.",
                    "vision": "Myopia (-1.5 both eyes). Wears corrective lenses.",
                    "bmi_at_booking": "22.4",
                    "bmi_at_delivery": "27.8",
                    "gbs_status": "Negative (tested at 36 weeks)",
                    "hiv_status": "Negative (tested at booking)",
                    "hep_b_status": "Non-reactive",
                    "syphilis_status": "Non-reactive",
                },
            ))

            # ── 7. Menstrual cycle tracking (post-postpartum) ─────────────
            print("[9/9] Creating cycle entries (3 complete + 1 current)…")

            # FormTemplate for cycle entry
            cycle_template = FormTemplate(
                id=uuid.uuid4(),
                slug="cycle-entry-seed-v1",
                context=FormContext.CYCLE_ENTRY,
                fields={
                    "fields": [
                        {"key": "flowLevel",  "type": "SINGLE_SELECT", "label": "Flow level",
                         "options": ["LIGHT", "MODERATE", "HEAVY", "VERY_HEAVY"], "required": True},
                        {"key": "clotLevel",  "type": "SINGLE_SELECT", "label": "Clot level",
                         "options": ["NONE", "SMALL", "LARGE"], "required": False},
                        {"key": "flags", "type": "MULTI_SELECT", "label": "Additional flags",
                         "options": ["LEAKED_THROUGH_CLOTHING", "CHANGED_AT_NIGHT",
                                     "SOAKED_WITHIN_2_HOURS"], "required": False},
                    ]
                },
                version="v1",
                is_active=False,    # seed-only template
                facility_id=None,
            )
            session.add(cycle_template)
            await session.flush()

            # Helper: compute PBAC score (mirrors cycle_service logic)
            def pbac_score(flow: str, clot: str = "NONE", flags: list[str] | None = None) -> int:
                flow_map  = {"LIGHT": 1, "MODERATE": 5, "HEAVY": 10, "VERY_HEAVY": 20}
                clot_map  = {"NONE": 0, "SMALL": 1, "LARGE": 5}
                flag_map  = {"LEAKED_THROUGH_CLOTHING": 5, "CHANGED_AT_NIGHT": 5, "SOAKED_WITHIN_2_HOURS": 10}
                score = flow_map.get(flow, 0) + clot_map.get(clot, 0)
                for f in (flags or []):
                    score += flag_map.get(f, 0)
                return score

            async def add_cycle(
                start: date,
                end: date | None,
                flow: str,
                clot: str = "NONE",
                flags: list[str] | None = None,
                pbac_items: list[tuple] | None = None,   # (date, PbacItemType, PbacSoakLevel|None, points)
            ) -> CycleEntry:
                flags = flags or []
                score = pbac_score(flow, clot, flags)
                sub = FormSubmission(
                    id=uuid.uuid4(),
                    template_id=cycle_template.id,
                    user_id=user.id,
                    context=FormContext.CYCLE_ENTRY,
                    answers={"flowLevel": flow, "clotLevel": clot, "flags": flags},
                    client_created_at=dt(start, 7),
                )
                session.add(sub)
                await session.flush()

                entry = CycleEntry(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    submission_id=sub.id,
                    start_date=start,
                    end_date=end,
                    pbac_score=score,
                )
                session.add(entry)
                await session.flush()

                for item_date, item_type, soak, points in (pbac_items or []):
                    session.add(PbacItem(
                        id=uuid.uuid4(),
                        cycle_entry_id=entry.id,
                        date=item_date,
                        item_type=item_type,
                        soak_level=soak,
                        point_value=points,
                    ))
                return entry

            # ── Cycle 1: first period after postpartum (slightly irregular, 5 days) ──
            c1 = await add_cycle(
                start=CYCLE1_START,
                end=CYCLE1_START + timedelta(days=4),
                flow="MODERATE",
                clot="SMALL",
                flags=[],
                pbac_items=[
                    (CYCLE1_START,                   PbacItemType.PAD, PbacSoakLevel.MODERATELY_SOAKED, 5),
                    (CYCLE1_START + timedelta(days=1), PbacItemType.PAD, PbacSoakLevel.FULLY_SOAKED,     10),
                    (CYCLE1_START + timedelta(days=2), PbacItemType.PAD, PbacSoakLevel.MODERATELY_SOAKED, 5),
                    (CYCLE1_START + timedelta(days=3), PbacItemType.PAD, PbacSoakLevel.LIGHTLY_SOAKED,   1),
                    (CYCLE1_START + timedelta(days=4), PbacItemType.PAD, PbacSoakLevel.LIGHTLY_SOAKED,   1),
                ],
            )

            # ── Cycle 2: 29 days later, 5 days, normal ────────────────────
            c2 = await add_cycle(
                start=CYCLE2_START,
                end=CYCLE2_START + timedelta(days=4),
                flow="MODERATE",
                clot="NONE",
                flags=[],
                pbac_items=[
                    (CYCLE2_START,                   PbacItemType.PAD, PbacSoakLevel.MODERATELY_SOAKED, 5),
                    (CYCLE2_START + timedelta(days=1), PbacItemType.PAD, PbacSoakLevel.FULLY_SOAKED,     10),
                    (CYCLE2_START + timedelta(days=2), PbacItemType.PAD, PbacSoakLevel.MODERATELY_SOAKED, 5),
                    (CYCLE2_START + timedelta(days=3), PbacItemType.PAD, PbacSoakLevel.LIGHTLY_SOAKED,   1),
                    (CYCLE2_START + timedelta(days=4), PbacItemType.PAD, PbacSoakLevel.LIGHTLY_SOAKED,   1),
                ],
            )

            # ── Cycle 3: 27 days later — current ongoing period ────────────
            # She is on Day 2 of her period right now. No end_date yet.
            # Only seed PBAC items for days that have already happened (<= today).
            cycle3_pbac = [
                (CYCLE3_START,                      PbacItemType.PAD, PbacSoakLevel.FULLY_SOAKED,      10),
                (CYCLE3_START + timedelta(days=1),  PbacItemType.PAD, PbacSoakLevel.FULLY_SOAKED,      10),
                (CYCLE3_START + timedelta(days=1),  PbacItemType.CLOT, None,                             5),
            ]
            c3 = await add_cycle(
                start=CYCLE3_START,
                end=None,                   # still ongoing — no end date
                flow="HEAVY",
                clot="SMALL",
                flags=["CHANGED_AT_NIGHT"],
                pbac_items=[(d, t, s, p) for d, t, s, p in cycle3_pbac if d <= TODAY],
            )

        # ── done ──────────────────────────────────────────────────────────
        print("\n✅ Seed complete!")
        print(f"   Phone      : {TEST_PHONE}")
        print(f"   Name       : {TEST_NAME}")
        print(f"   County     : {TEST_COUNTY}")
        print(f"   User ID    : {user.id}")
        print(f"   Baby       : {baby.name}  (DOB: {BIRTH_DATE})")
        print(f"   Pregnancy  : {LMP} → {DUE_DATE} (ended {BIRTH_DATE})")
        print(f"   Current    : NOT_PREGNANT — tracking menstrual cycle")
        print(f"   Cycles     : {CYCLE1_START} (done) / {CYCLE2_START} (done) / {CYCLE3_START} (ACTIVE — Day {(TODAY - CYCLE3_START).days + 1})")


if __name__ == "__main__":
    asyncio.run(seed())
