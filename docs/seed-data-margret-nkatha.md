# Seed Data — Margret Nkatha (Pitch Demo User)

Rich, coherent, single-user dataset for the investor/pitch demo. Covers **Auth → Profile → Cycle Tracking → Pregnancy Tracker → Postpartum & Baby Tracker**, built against the *mother-facing* mobile API contracts in `docs/auth.md`, `docs/profile.md`, `docs/cycle-tracking.md`, `docs/pregnancy.md`, `docs/postpartum.md`.

**All record IDs (`id`, `submission_id`, etc.) are server/DB-generated (`gen_random_uuid()` in Postgres, or whatever the real `POST` endpoint returns) — nothing below is a hardcoded UUID.** Every place an ID is needed before it exists, this doc uses a `{{ref_token}}` placeholder. Generate the row, capture the real UUID the server returns, and substitute it everywhere else that token appears. If you are seeding by calling the live API in sequence, this happens naturally (each `POST` response gives you the ID for the next step). If you are seeding by inserting directly into Postgres, generate the UUID yourself (`gen_random_uuid()`) before the insert and use that same value for every FK reference.

---

## 0. The Story (why this shape)

A single mother's timeline spanning ~2.3 years, so every feature module has deep, believable history by "today" (**2026-07-21**):

| Phase | Dates | What it demos |
|---|---|---|
| Cycle tracking, pre-pregnancy #1 | 2024-04 → 2024-08 | Cycle Tracker: history, regular ~29-day cycles, symptoms, PBAC |
| **Pregnancy #1** (first pregnancy) | LMP 2024-08-01 → ends 2025-05-14 (live birth) | Pregnancy Tracker: full completed journey, now historical |
| **Baby #1 — Zawadi Nkatha** born 2025-05-14, now 14 months old | 2025-05 → today | Postpartum & Baby Tracker: maternal recovery, EPDS, baby vitals, milestones, vaccination schedule (with one clean "upcoming" dose) |
| Cycle tracking, inter-pregnancy | 2025-09 → 2026-01 | Cycle Tracker: postpartum resumption of cycles, still regular |
| **Pregnancy #2** (current, active) | LMP 2026-02-02, due 2026-11-09, **week 24 today** | Pregnancy Tracker: live dashboard — week info, vitals trend, ANC schedule (past visits completed, next one upcoming), risk score history with a resolved mid-pregnancy blip |

`current_stage` on the profile should end up **`PREGNANT`** (Pregnancy #2 is active). Baby #1's postpartum/baby data stays fully reachable through its own `/postpartum/...` endpoints regardless of the mother's current stage — use the app's dev-only `StagePreviewSwitcher` during the pitch to flip the Track tab to Postpartum/Cycle views on demand ([[binticare-feature-arc-pattern]] / see project memory), no backend state change required.

---

## 1. Prerequisite: Facility

Profile, pregnancy ANC visits, and baby vaccinations all reference a facility. Use (or create via `POST /api/v1/facilities/register` or a direct `facilities` insert) a Meru-based facility:

```json
{
  "name": "Meru Teaching and Referral Hospital",
  "type": "PUBLIC",
  "county": "Meru",
  "address": "Meru–Nkubu Rd, Meru Town",
  "phone_number": "+254612030150",
  "latitude": 0.0470,
  "longitude": 37.6559,
  "services_offered": ["ANTENATAL_CARE", "DELIVERY", "POSTNATAL_CARE", "IMMUNIZATION"],
  "readiness": { "bloodBankStocked": true, "maternityBedsAvailable": 20 }
}
```

→ `{{facility_id}}` = the generated facility UUID. Used everywhere below as "preferred facility," "place of birth," and "vaccinating facility."

---

## 2. Auth — `POST /api/v1/auth/register`

```json
{
  "phone_number": "+254720168641",
  "full_name": "Margret Nkatha",
  "role": "USER",
  "password": "Nkatha@55",
  "date_of_birth": "1996-04-18",
  "gender": "FEMALE",
  "preferred_language": "en",
  "county": "Meru",
  "profile_photo_url": null
}
```

→ `{{user_id}}` = the generated user UUID.

**Demo login credentials:**
| Field | Value |
|---|---|
| Phone number | `0720168641` (`+254720168641`) |
| Password | `Nkatha@55` |

Account should be created well in the past for a believable "member since" — if `created_at` isn't overridable via the register endpoint, patch it directly in Postgres to `2024-03-20T08:00:00Z`.

---

## 3. Profile — `POST /api/v1/profile/me`

```json
{
  "current_stage": "PREGNANT",
  "emergency_sharing_preference": "ALWAYS_SHARE",
  "notification_preference": "BOTH",
  "emergency_contact": {
    "name": "Kaburu Mwenda",
    "relationship": "Husband",
    "phone": "+254733221144"
  },
  "companion_preference": "BOTH",
  "typical_cycle_length_days": 29,
  "home_address_name": "Kaaga, Meru Town",
  "home_location_lat": "0.0470",
  "home_location_lng": "37.6559",
  "live_location_sharing_enabled": true,
  "preferred_facility_id": "{{facility_id}}"
}
```

→ `{{profile_id}}`. `ALWAYS_SHARE` + `live_location_sharing_enabled: true` is deliberate — it makes the Emergency SOS flow demo meaningfully during the pitch (auto-notifies the facility + emergency contact with no extra "ask first" step).

After Pregnancy #2 is started (§5.2), request a personal doctor so the Care Team card isn't empty:

`POST /api/v1/profile/me/personal-doctor-request`
```json
{ "facility_id": "{{facility_id}}" }
```
This sets `personal_doctor_request_status: "PENDING"`. If you want the Care Team card to show a fully **assigned** doctor (richer demo) instead of "pending," have a facility-admin/clinician seed assign one via the web/clinician-side flow — that's outside this mobile-API doc's scope.

### 3.1 Medical history (⚠️ no mother-facing create endpoint)

`medical_history` only appears read-only, via `GET /api/v1/profile/qr/scan/{token}` — it's written by clinicians, not this API. To make the QR Passport demo show real data, insert directly into Postgres (or via a clinician-side seed) using this shape:

```json
{
  "patient_user_id": "{{user_id}}",
  "blood_type": "O",
  "rh_factor": "+",
  "allergies": [],
  "chronic_conditions": [],
  "current_medications": ["Folic acid 5mg daily", "Ferrous sulphate 200mg daily"],
  "surgical_history": [],
  "previous_pregnancies": 1,
  "previous_outcomes": ["LIVE_BIRTH"],
  "family_history": ["Hypertension — maternal grandmother"],
  "custom_fields": null,
  "created_by": "{{facility_clinician_user_id}}",
  "last_updated_by": "{{facility_clinician_user_id}}"
}
```

---

## 4. Cycle Tracking (`docs/cycle-tracking.md`)

Fetch the real `templateSlug` from `GET /entries/form-template` first — assumed `"tmpl_cycle_entry_v1"` below, matching the doc's example. Symptom logging always uses `"tmpl_symptom_entry_v1"`.

### 4.1 Phase A — pre-Pregnancy #1 (regular ~29-day cycles)

`POST /entries` for each row (`answers` shape: `flowLevel`, `clotLevel`, `flags`):

| Ref | `startDate` | flowLevel | clotLevel | flags | PBAC items? |
|---|---|---|---|---|---|
| `cycleA1` | 2024-04-02 | MODERATE | NONE | `[]` | — |
| `cycleA2` | 2024-05-01 | HEAVY | SMALL | `[]` | ✅ see below |
| `cycleA3` | 2024-05-30 | MODERATE | NONE | `[]` | — |
| `cycleA4` | 2024-06-28 | MODERATE | NONE | `["IRREGULAR_CLOTS"]` → use `[]` if that flag isn't in the live enum | ✅ see below |
| `cycleA5` | 2024-08-01 | LIGHT | NONE | `[]` | — *(this is also Pregnancy #1's LMP — see §5.1)* |

**PBAC items** — `POST /entries/{entry_id}/pbac-items`, `itemType: PAD`, standard point table (light=1, moderate=5, full=20):

- `cycleA2` (2024-05-01, 3-day heavy period): day1 `FULLY_SOAKED`/20, day2 `MODERATELY_SOAKED`/5, day3 `LIGHTLY_SOAKED`/1 → total 26 (well under the 80 HMB threshold — confirm via `GET /entries/{id}/pbac-score`).
- `cycleA4` (2024-06-28): day1 `MODERATELY_SOAKED`/5, day2 `LIGHTLY_SOAKED`/1 → total 6.

**Symptoms** — `POST /symptoms` (`answers`: `symptoms`, `notes`), one per cycle plus a couple of standalone PMS-only days:

| Ref | `date` | symptoms | notes |
|---|---|---|---|
| symA1 | 2024-04-02 | `["CRAMPS", "BLOATING"]` | "Mild cramps, manageable" |
| symA2 | 2024-04-29 | `["MOOD_SWINGS"]` | "A bit irritable before period" |
| symA3 | 2024-05-01 | `["CRAMPS", "FATIGUE"]` | "Heavier flow today" |
| symA4 | 2024-05-30 | `["BLOATING"]` | — |
| symA5 | 2024-06-26 | `["HEADACHE"]` | "Mild headache, 2 days before period" |
| symA6 | 2024-06-28 | `["CRAMPS"]` | — |
| symA7 | 2024-08-01 | `["FATIGUE", "NAUSEA"]` | "Felt off, later found out I was pregnant" |

### 4.2 Phase B — inter-pregnancy (postpartum resumption, 2025-09 → 2026-01)

| Ref | `startDate` | flowLevel | clotLevel | flags |
|---|---|---|---|---|
| cycleB1 | 2025-09-10 | LIGHT | NONE | `[]` |
| cycleB2 | 2025-10-12 | MODERATE | NONE | `[]` |
| cycleB3 | 2025-11-08 | MODERATE | NONE | `[]` |
| cycleB4 | 2025-12-06 | MODERATE | SMALL | `[]` |
| cycleB5 | 2026-01-04 | MODERATE | NONE | `[]` — *this is also Pregnancy #2's LMP, 2026-02-02, is the next expected-but-missed period* |

**Symptoms:**

| Ref | `date` | symptoms | notes |
|---|---|---|---|
| symB1 | 2025-09-10 | `["FATIGUE"]` | "First period since Zawadi was born" |
| symB2 | 2025-10-10 | `["MOOD_SWINGS"]` | — |
| symB3 | 2025-11-08 | `["CRAMPS"]` | — |
| symB4 | 2025-12-04 | `["BLOATING", "HEADACHE"]` | — |
| symB5 | 2026-01-04 | `["CRAMPS", "FATIGUE"]` | — |
| symB6 | 2026-01-29 | `["NAUSEA"]` | "Missed period, feeling nauseous" — right before discovering Pregnancy #2 |

**PBAC** — one entry for realism: `cycleB3` (2025-11-08): day1 `MODERATELY_SOAKED`/5, day2 `LIGHTLY_SOAKED`/1 → total 6.

With ≥2 entries in each phase, `GET /predictions` and `GET /trends` compute for real — no manual seeding needed there. `typical_cycle_length_days: 29` on the profile (§3) matches this data's actual average.

---

## 5. Pregnancy Tracker (`docs/pregnancy.md`)

### 5.1 Pregnancy #1 — historical, ended

`POST /pregnancy/start`
```json
{
  "dateInputType": "LMP",
  "lastMenstrualPeriod": "2024-08-01",
  "isFirstPregnancy": true
}
```
→ `{{pregnancy1_id}}`. Due date computes to **2025-05-08**.

**Vitals** — `POST /pregnancy/vitals` (fetch real `templateSlug` first; assumed `"tmpl_preg_vitals_v1"`), all within normal range (clean, low-risk pregnancy):

| Ref | date (`clientCreatedAt`) | systolicBp | diastolicBp | weightKg | symptoms |
|---|---|---|---|---|---|
| vit1a | 2024-09-15 | 112 | 72 | 62.0 | `["NAUSEA"]` |
| vit1b | 2024-11-10 | 110 | 70 | 65.5 | `[]` |
| vit1c | 2025-01-05 | 114 | 74 | 69.0 | `[]` |
| vit1d | 2025-02-20 | 116 | 76 | 71.5 | `["BACK_PAIN"]` |
| vit1e | 2025-04-10 | 118 | 78 | 73.5 | `[]` |
| vit1f | 2025-05-01 | 116 | 74 | 74.8 | `["SWELLING"]` — mild, near-term, expected |

**ANC visits** — auto-generated by `POST /start` from the standard MOH pathway. Since this pregnancy is fully in the past, mark every visit `COMPLETED` (clinician-side action, `docs/web/pregnancy-clinical.md` — or a direct `UPDATE anc_visits SET status='COMPLETED'` for rows with `scheduled_at < now()`):

| Milestone | ~scheduled | purpose |
|---|---|---|
| ANC 1 | 2024-09-12 | First Trimester Screening |
| ANC 2 | 2024-11-07 | Second Trimester Check |
| ANC 3 | 2025-01-02 | Growth & BP Monitoring |
| ANC 4 | 2025-02-27 | Third Trimester Screening |
| ANC 5 | 2025-03-27 | Fetal Position Check |
| ANC 6 | 2025-04-10 | Pre-delivery Assessment |
| ANC 7 | 2025-04-24 | Final Check |
| ANC 8 | 2025-05-01 | Delivery Readiness |

**Risk score** — computed server-side from the vitals above; expect **LOW** throughout (no seeding action).

`POST /pregnancy/end`
```json
{ "endedAt": "2025-05-14T11:20:00Z", "outcome": "LIVE_BIRTH" }
```

### 5.2 Pregnancy #2 — current, active (week 24 today)

`POST /pregnancy/start`
```json
{
  "dateInputType": "LMP",
  "lastMenstrualPeriod": "2026-02-02",
  "isFirstPregnancy": false
}
```
→ `{{pregnancy2_id}}`. Due date computes to **2026-11-09**. On 2026-07-21 this is **week 24, trimester 2**.

**Vitals:**

| Ref | date | systolicBp | diastolicBp | weightKg | symptoms | notes |
|---|---|---|---|---|---|---|
| vit2a | 2026-02-20 | 110 | 70 | 60.0 | `["FATIGUE"]` | booking visit |
| vit2b | 2026-03-20 | 112 | 72 | 61.5 | `[]` | |
| vit2c | 2026-04-17 | 114 | 74 | 63.0 | `[]` | |
| vit2d | 2026-05-15 | 128 | 84 | 65.5 | `["SWELLING"]` | **flagged** — mild elevated BP, demonstrates the risk-trend blip |
| vit2e | 2026-06-12 | 118 | 76 | 67.0 | `[]` | resolved back to normal |
| vit2f | 2026-07-10 | 116 | 74 | 68.5 | `[]` | most recent, normal |

`vit2d` should come back `is_flagged: true` with a server `flagged_reasons` entry (e.g. "Elevated blood pressure") given the real `FormTemplate`'s flagging thresholds — verify against the live template.

**Risk score history** (server-computed from the vitals above — expected trajectory, no direct seeding needed):

| calculatedAt | score | level |
|---|---|---|
| 2026-02-20 | 0 | LOW |
| 2026-03-20 | 0 | LOW |
| 2026-04-17 | 0 | LOW |
| 2026-05-15 | ~15 | MEDIUM |
| 2026-06-12 | ~5 | LOW |
| 2026-07-10 | 0 | LOW |

**ANC visits** (auto-generated on start, standard 8-contact MOH model):

| Milestone | ~scheduled | Expected status *today* |
|---|---|---|
| ANC 1 | 2026-03-30 (wk 8) | COMPLETED |
| ANC 2 | 2026-04-27 (wk 12) | COMPLETED |
| ANC 3 | 2026-05-25 (wk 16) | COMPLETED |
| ANC 4 | 2026-06-22 (wk 20) | COMPLETED |
| ANC 5 | 2026-08-03 (wk 26) | **SCHEDULED (upcoming)** — leave as-is, don't mark complete |
| ANC 6 | 2026-08-31 (wk 30) | SCHEDULED |
| ANC 7 | 2026-09-28 (wk 34) | SCHEDULED |
| ANC 8 | 2026-10-19 (wk 37) | SCHEDULED |

Mark the first four `COMPLETED` (clinician-side, same mechanism as §5.1) with brief `summary` text (e.g. "All normal, baby growing well") for a polished history view.

**Nutrition guidance** (`GET /nutrition-guidance`) is platform-wide reference content, not per-user — just confirm at least one item exists per category (`IRON`, `FOLIC_ACID`, `HYDRATION`, `FOODS_TO_AVOID`, `HEALTHY_SNACKS`) in whatever seeds that table; nothing user-specific to add here.

**Week info** (`GET /week-info`) is derived from the active pregnancy's dates — no seeding action; confirm week-24 content exists in whatever seeds `pregnancy_week_info` reference data.

---

## 6. Postpartum & Baby Tracker (`docs/postpartum.md`) — Baby #1

### 6.1 Baby profile — `POST /postpartum/baby/profile`

```json
{
  "name": "Zawadi Nkatha",
  "dateOfBirth": "2025-05-14",
  "timeOfBirth": "11:20",
  "sex": "FEMALE",
  "birthWeightKg": 3.4,
  "birthLengthCm": 50,
  "deliveryType": "VAGINAL",
  "placeOfBirth": "Meru Teaching and Referral Hospital",
  "notes": "Healthy, breastfeeding well",
  "pregnancyId": "{{pregnancy1_id}}"
}
```
→ `{{baby1_id}}`. This call also auto-generates the vaccination schedule.

### 6.2 Baby vitals — `POST /postpartum/baby/{baby_id}/vitals`

(Fetch real `templateId` from `GET /baby/vitals/form-template` first; assumed `"tmpl_baby_vitals_v1"`.)

| Ref | date | temperatureCelsius | weightKg | feedingType |
|---|---|---|---|---|
| bvit1 | 2025-05-15 | 36.9 | 3.3 | BREASTFEEDING |
| bvit2 | 2025-06-25 | 36.7 | 4.8 | BREASTFEEDING |
| bvit3 | 2025-08-14 | 36.8 | 6.2 | BREASTFEEDING |
| bvit4 | 2025-11-14 | 36.6 | 7.8 | MIXED |
| bvit5 | 2026-02-14 | 36.9 | 8.6 | MIXED |
| bvit6 | 2026-05-14 | 36.8 | 9.5 | SOLIDS |
| bvit7 | 2026-07-10 | 36.7 | 10.1 | SOLIDS |

All within normal range — no vitals alerts should trigger (`GET /baby/{baby_id}/vitals/alerts` returns empty), matching the "clean" brief. Verify `feedingType`/field keys against the live template — the doc's example only confirms `temperatureCelsius` and `feedingType` exist.

### 6.3 Milestones — `POST /postpartum/baby/{baby_id}/milestones`

| category | title | achievedAt |
|---|---|---|
| MOVEMENT | Held head up | 2025-06-20 |
| SOCIAL | First social smile | 2025-06-10 |
| COGNITIVE | Tracks objects with eyes | 2025-06-05 |
| LANGUAGE | Coos and gurgles | 2025-07-01 |
| MOVEMENT | Rolled over | 2025-08-20 |
| SOCIAL | Laughs out loud | 2025-08-05 |
| LANGUAGE | Babbles "mama"/"baba" sounds | 2025-10-15 |
| MOVEMENT | Sat without support | 2025-11-20 |
| SOCIAL | Shows stranger anxiety, clings to mum | 2025-11-10 |
| COGNITIVE | Object permanence — looks for hidden toy | 2025-11-25 |
| MOVEMENT | Crawling | 2026-02-14 |
| LANGUAGE | Says first word — "mama" | 2026-02-20 |
| SOCIAL | Waves bye-bye | 2026-03-01 |
| COGNITIVE | Points at objects of interest | 2026-03-15 |
| MOVEMENT | First steps | 2026-05-20 |
| LANGUAGE | Says 2–3 words | 2026-06-01 |
| COGNITIVE | Stacks two blocks | 2026-06-20 |

17 milestones across all 4 categories spanning the full 14 months — rich "memory book" view. Leave `photoUrl` null unless you have real demo photo assets to attach.

### 6.4 Vaccination schedule — KEPI pathway, auto-generated on §6.1

For each dose already due, `PUT /postpartum/baby/{baby_id}/vaccinations/{visit_id}/mark-given` (⚠️ **`PUT`, not `POST`** — the doc's endpoint is correct, but a past implementation bug in this app called `.post()` here; confirm the client uses `.put()`):

| Age milestone | Vaccines | `givenAt` | facilityId | batchNumber | Status today |
|---|---|---|---|---|---|
| Birth | BCG, OPV0 | 2025-05-14T11:30:00Z | `{{facility_id}}` | BCG-2025-0442 | GIVEN |
| 6 weeks | DPT-HepB-Hib1, OPV1, PCV1, Rota1 | 2025-06-25T09:00:00Z | `{{facility_id}}` | PENTA1-2025-1187 | GIVEN |
| 10 weeks | DPT-HepB-Hib2, OPV2, PCV2, Rota2 | 2025-07-23T09:15:00Z | `{{facility_id}}` | PENTA2-2025-1390 | GIVEN |
| 14 weeks | DPT-HepB-Hib3, OPV3, PCV3, IPV | 2025-08-20T09:10:00Z | `{{facility_id}}` | PENTA3-2025-1602 | GIVEN |
| 9 months | Measles-Rubella1, Yellow Fever, Vitamin A | 2026-02-14T10:00:00Z | `{{facility_id}}` | MR1-2026-0298 | GIVEN |
| 18 months | Measles-Rubella2 | 2026-11-14 | — | — | **leave un-marked — upcoming** |

Leaving the 18-month dose unmarked (baby is only 14 months old today) gives a clean single "upcoming" row instead of a messy overdue one.

### 6.5 Maternal check-ins — `POST /postpartum/maternal-checkins`

(Fetch real `templateId` from `GET /maternal-checkins/form-template` first; assumed `"tmpl_postpartum_checkin_v1"`.)

| Ref | date | bleedingLevel | painLevel | symptoms |
|---|---|---|---|---|
| chk1 | 2025-05-16 | HEAVY | 5 | `["FATIGUE", "CRAMPING"]` |
| chk2 | 2025-05-21 | MODERATE | 3 | `["FATIGUE"]` |
| chk3 | 2025-05-28 | LIGHT | 2 | `[]` |
| chk4 | 2025-06-25 | NONE | 0 | `[]` |

A clean recovery arc: heavy → moderate → light → fully resolved by the 6-week check.

### 6.6 EPDS depression screening — `POST /postpartum/depression-screening`

Two screenings, both reassuring/low-risk (clean pitch narrative — demonstrates the feature without an alarming flag):

**Screening 1 — 2025-05-28 (week 2):**
```json
{
  "responses": [
    { "questionId": "q1", "answerValue": 1 },
    { "questionId": "q2", "answerValue": 1 },
    { "questionId": "q3", "answerValue": 0 },
    { "questionId": "q4", "answerValue": 0 },
    { "questionId": "q5", "answerValue": 0 },
    { "questionId": "q6", "answerValue": 1 },
    { "questionId": "q7", "answerValue": 0 },
    { "questionId": "q8", "answerValue": 1 },
    { "questionId": "q9", "answerValue": 0 },
    { "questionId": "q10", "answerValue": 0 }
  ]
}
```
→ `totalScore` 4, `suggestsSupportBeneficial: false`, `immediateConcernFlag: false`.

**Screening 2 — 2025-06-25 (week 6):**
```json
{
  "responses": [
    { "questionId": "q1", "answerValue": 0 },
    { "questionId": "q2", "answerValue": 1 },
    { "questionId": "q3", "answerValue": 0 },
    { "questionId": "q4", "answerValue": 0 },
    { "questionId": "q5", "answerValue": 0 },
    { "questionId": "q6", "answerValue": 0 },
    { "questionId": "q7", "answerValue": 0 },
    { "questionId": "q8", "answerValue": 1 },
    { "questionId": "q9", "answerValue": 0 },
    { "questionId": "q10", "answerValue": 0 }
  ]
}
```
→ `totalScore` 2 — trending down, healthy resolution.

### 6.7 Clinic visits schedule (`GET /clinic-visits/schedule`)

Read-only/auto-derived from the check-in, vitals, and vaccination records above — no direct seeding action, listed here for reference of the expected view:

| label | scheduledAt | covers | status |
|---|---|---|---|
| 2 Week Checkup | 2025-05-28 | MOTHER, BABY | COMPLETED |
| 6 Week Checkup | 2025-06-25 | MOTHER, BABY | COMPLETED |
| 6 Month Growth Visit | 2025-11-14 | BABY | COMPLETED |
| 12 Month Growth & Immunization Review | 2026-05-14 | BABY | COMPLETED |
| 18 Month Vaccination Visit | 2026-11-14 | BABY | UPCOMING |

---

## 7. Seeding Order (respects FK dependencies)

1. Facility (§1) → `{{facility_id}}`
2. Register user (§2) → `{{user_id}}`
3. Create profile (§3) → `{{profile_id}}`; insert medical history directly (§3.1)
4. Cycle Phase A: 5 entries + PBAC items + 7 symptom logs (§4.1)
5. Pregnancy #1: start → vitals ×6 → (clinician marks ANC visits complete) → end (§5.1)
6. Cycle Phase B: 5 entries + PBAC item + 6 symptom logs (§4.2)
7. Baby #1 profile (§6.1) → `{{baby1_id}}` (auto-generates vaccination schedule)
8. Baby vitals ×7 (§6.2)
9. Milestones ×17 (§6.3)
10. Mark 5 vaccination doses given, leave 18-month dose upcoming (§6.4)
11. Maternal check-ins ×4 (§6.5)
12. EPDS screenings ×2 (§6.6)
13. Pregnancy #2: start (§5.2) → vitals ×6 → (clinician marks first 4 ANC visits complete)
14. Request personal doctor (§3, end)
15. Regenerate/patch `created_at` timestamps if your seed path doesn't accept them inline

---

## 8. Verify before the live pitch

Two real backend/doc mismatches were found during this app's own integration work — worth a smoke test before presenting:

1. **`POST /v1/pregnancy/vitals` has an open bug**: was observed returning a raw `500` regardless of payload correctness. Test §5.1/§5.2's vitals inserts against the real backend well before the pitch; if still broken, insert those rows directly into Postgres as a fallback so the Vitals History / Risk Score screens still have data to render.
2. **Vaccination `mark-given` is `PUT`, not `POST`** — confirm whichever seeding path you use (API calls vs. a script) sends the right verb, or the six §6.4 rows will silently fail to mark as given.
3. Dynamic form (`fields`) shapes for vitals/check-in templates have previously come back from the real backend in an undocumented, differently-cased shape than `pregnancy.md`/`postpartum.md` show. If you're driving the seed through the real `FormTemplate` fetch rather than hardcoding the `templateSlug`/`templateId` strings above, sanity-check the field keys actually match (`systolicBp`, `bleedingLevel`, etc.) before submitting `answers`.
