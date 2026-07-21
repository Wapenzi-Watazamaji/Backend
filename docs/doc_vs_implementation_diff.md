# `docs/doc.md` vs. Actual Implementation — Differences

Comparison of `docs/doc.md` (Mobile API Documentation, v1.1 Draft) against the actual FastAPI codebase (`app/`). The doc describes an aspirational/older design in several places; the code has drifted from it (or moved ahead of it) in others.

---

## Global

- **Base path is wrong.** Doc says base URL is `.../api`. Actual mount is `app.include_router(api_router, prefix="/api/v1")` (`app/main.py:53`) — every endpoint in the doc is missing `/v1`.
- **Response envelope has an extra field.** Doc shows `{success, data, meta, error}`. Actual `APIResponse` (`app/utils/exceptions.py`) also always includes `message`. Also `data`/`meta` default to `{}` when omitted, not `null` as the doc's failure example shows.
- **Roles**: doc's `MOTHER` role is actually called `USER` in `UserRole` (`app/models/user.py`). `CLINICIAN`/`FACILITY_ADMIN` match.
- **Offline sync (`clientGeneratedId`) is not universal.** Doc claims every creating `POST` accepts it. In reality it only appears in cycle, pregnancy-vitals, and postpartum schemas — not in referrals, reminders, education, labour readings, milestones, vaccinations, emergencies, etc.
- **`FormSubmission`/`FormTemplate` is not the universal backing model** the doc claims. It genuinely backs cycle entries/symptoms, but pregnancy vitals is its own `PregnancyVitalsEntry` (wraps a `FormSubmission` via FK, adds its own `is_flagged`), and postpartum baby vitals/maternal check-ins/EPDS use their own dedicated tables/response models (`MaternalCheckinRead`, `EpdsScreeningRead`, etc.), not a generic `FormSubmissionRead`.

---

## Auth

- `POST /auth/forgot-password` and `POST /auth/reset-password` **don't exist** — no OTP/password-reset flow in code at all.
- Code has undocumented `GET /auth/me` and `GET /auth/me/landing-summary`.

---

## Profile

- Doc's `GET /profile/lookup/{qrToken}` + `GET /profile/lookup/{qrToken}/full-history` → actual is a single `GET /profile/qr/scan/{token}` endpoint, no separate full-history variant.
- `GET /profile/access-log` **doesn't exist** — no access-log tracking at all.
- `GET`/`PUT /profile/preferred-units` **don't exist** — `Profile` model has a single `preferred_facility_id`, not a list.
- Consent endpoints differ entirely: doc's `POST/GET/DELETE /profile/consent` → actual is `GET /profile/me/consents` + `PUT /profile/me/consents/{grantee_id}/revoke` (no create endpoint here; revoke is by grantee, not consent ID).
- `GET /profile/personal-doctor` (status) **doesn't exist** as its own endpoint.
- `POST /profile/personal-doctor/request` → actual path is `POST /profile/me/personal-doctor-request`.
- `PUT /profile/emergency-sharing-preference` **doesn't exist** standalone. Also the enum differs: doc's `AUTO_SHARE|ASK_FIRST|MANUAL` vs code's `SharingPreference: ASK_FIRST|ALWAYS_SHARE|NEVER_SHARE`.
- `POST /profile/me/photo` **doesn't exist**.
- `Consent` entity shape is different: doc has `granteeType: FACILITY|CLINICIAN`. Code's `ConsentType` is `ASK_EVERYTIME|AUTO_SHARE|FACILITY_AUTO_SHARE` — a sharing-mode enum, not a grantee-type enum — and it's reused for AI-companion consent too (see AI section), a use case the doc never mentions.

---

## Menstrual & Cycle Tracker

Closest match to the doc. One path difference: `POST /cycles/hmb-status/acknowledge` → actual is `POST /cycles/hmb-acknowledge`.

---

## Pregnancy Journey Tracker

- `POST /pregnancy/anc-visits/manual` → actual requires `{patient_id}` in the path (`/anc-visits/manual/{patient_id}`), facility comes from context, not body.
- `PUT /pregnancy/anc-visits/{id}` → actual is `PUT /pregnancy/anc-visits/{visit_id}/patient/{user_id}` (extra required path param).
- Undocumented: `PUT /pregnancy/patients/{patient_id}/risk-score/override`.

---

## Labour & Birth Monitor

Close match. Undocumented additions: `GET /labour/active`, `GET /labour/alerts-summary`, `PUT /labour/sessions/{id}/room`.

---

## Postpartum & Baby Tracker

- Doc assumes **one baby per mother** (`GET/PUT /postpartum/baby/profile`). Code supports **multiple babies**: `POST /baby/profile`, but reads are `GET /baby/profiles` and `GET /baby/profiles/{baby_id}`.
- Vitals/milestones/vaccinations are all nested under `/baby/{baby_id}/...` in code, vs doc's flat `/postpartum/baby/vitals`, `/postpartum/baby/milestones`, `/postpartum/baby/vaccinations`.
- `PUT /postpartum/baby/vaccinations/{id}/mark-given` → actual is `PUT /postpartum/baby/{baby_id}/vaccinations/{visit_id}/mark-given`.
- Undocumented clinician/facility endpoints: `GET /postpartum/patients/{patient_id}/babies|epds|maternal-checkins`, `GET /postpartum/postpartum-alerts/summary`, `GET /postpartum/postpartum-patients`.
- Minor bug smell (not a doc issue but worth flagging): `create_baby_vitals`'s `response_model` is `MaternalCheckinRead`, reused instead of a baby-vitals-specific model.

---

## Universal Referral Network & Facilities

- `POST /facilities` (doc, authenticated `FACILITY_ADMIN`) → actual `POST /facilities/register` has **no auth dependency at all** — it's a public self-service signup, not an authenticated admin action.
- Doc's per-ID facility management (`PUT /facilities/{id}`, `PUT /facilities/{id}/availability`, staff CRUD under `/facilities/{id}/staff`) → actual uses a "my facility" pattern (`/facilities/current`, `/facilities/current/stats`, `/facilities/staff`) resolved from auth context, not path IDs. There's no dedicated `/availability` endpoint at all.
- `DELETE /facilities/{id}/staff/{userId}` **doesn't exist** — deactivation is `PUT /facilities/staff/{staff_id}` (via facility_admin) or `.../deactivate`, no hard delete.
- `GET /facilities/nearby`: doc's `latitude`/`longitude`/`transportMode`/`radiusKm` params and `estimatedTimeToCareMinutes`/`transportModeUsed` response fields (the "time to nearest care" design) → actual uses `lat`/`lng`/`radius_km`/`limit`, no transport mode, no time-to-care calculation, just distance.
- **Emergencies and referrals are two separate systems in code**, not one. Doc models an emergency as a `Referral` with `isEmergency: true` via `POST /referrals`. Code has a dedicated `EmergencyRequest` model and `/emergencies` route group (`POST /emergencies`, `GET /emergencies/my-requests`, `GET /emergencies/inbox`, `PUT /emergencies/{id}`), entirely separate from `/referrals`.
- `GET /referrals/{id}/summary-document` (PDF) **doesn't exist**.
- Undocumented: `GET /referrals/inbox/incoming`, `GET /referrals/inbox/outgoing`.

---

## Reminders, Notifications & SMS

Best match of any module — paths and shapes line up closely. One addition: an undocumented WebSocket, `GET /notifications/ws/{user_id}`, for live push.

---

## Education & Community Engagement

No significant differences found — content/events/feed endpoints match the doc.

---

## AI Assistant & Personal Doctor Chat

This section has diverged the most:

- Doc's `/assistant/*` namespace (conversations, `POST .../messages`, `/assistant/settings` with `voiceStyle`/`conversationStyle`, `DELETE /assistant/conversations`) **doesn't exist**.
- Actual: `/ai/consent` (POST/DELETE), `/ai/context-summary` (GET), and `/chat/conversations` + `/chat/conversations/{id}/messages` (read-only REST) — **sending a message has no REST endpoint at all**; it's WebSocket-only (`/chat/ws`).
- No settings endpoint for voice/conversation style. Instead there's a `CompanionPreference` enum (`AI_DOC|PERSONAL_DOCTOR|BOTH|NONE`) on `Profile` — a different concept (which companion, not response tone).
- **Personal Doctor Chat is entirely unimplemented.** No `/doctor-chat/*` routes exist anywhere.
- "AI Companion consent" (`/ai/consent`) is undocumented functionality, riding on the same `Consent` entity the doc defines for facility sharing.

---

## Facility-Managed Patients & Manual Entry (Module 11)

- `POST /facility-admin/patients` → actual is `POST /facility-admin/enroll-patient` (different name; facility comes from auth context, not body).
- `GET /facility-admin/patients` filters differ: doc's `assignedClinicianId=unassigned` → actual is a separate endpoint, `GET /facility-admin/unassigned-patients`; actual list endpoint instead takes `search`/`tab`.
- `PUT .../assign-clinician` body has no `reason` field in code (no `GENERAL_ASSIGNMENT`/`PERSONAL_DOCTOR_REQUEST` distinction) — so the doc's described side effect of auto-updating `personalDoctorRequestStatus` via this path isn't wired up as documented.
- `POST /facility-admin/patients/{patientId}/entries/{context}` (staff submitting a form on a patient's behalf) **doesn't exist**.
- `GET /facility-admin/patients/{patientId}/full-history` **doesn't exist**.
- `POST /facility-admin/form-templates` **doesn't exist** at that path — template creation instead lives in a separate module, `POST /templates/forms` (plus undocumented `GET /templates/forms`, `GET /templates/care-pathways`, `PUT /templates/forms/{id}`).
- Large amount of undocumented facility-admin functionality: `POST /facility-admin/bulk-reassign`, `GET /facility-admin/overview`, `GET /facility-admin/clinician-workloads`, `GET /facility-admin/staff`, `POST /facility-admin/register-staff`, `POST .../resend-invite`, `PUT .../capacity`, `PUT .../deactivate`.

---

## Entire modules missing from the doc

- `app/api/routes/medical_history_routes.py` — full medical-history module (`/medical-history/*`), not mentioned anywhere.
- `app/api/routes/clinician_dashboard_routes.py` — 13-endpoint web dashboard API (`/dashboard/*`).
- `app/api/routes/report_routes.py` — reporting/export module (`/reports/*`).
- `app/api/routes/user_routes.py` exists but **isn't even registered** in `api_router` — dead code, also absent from the doc.

---

## Takeaway

`doc.md` reads as an idealized/earlier API design rather than a source of truth for integration. Several other per-module docs exist in `docs/` (`pregnancy.md`, `Postpartum.md`, `Universal_Referral_Network.md`, etc.) that may track the actual implementation more closely and could be worth checking against the code next.
