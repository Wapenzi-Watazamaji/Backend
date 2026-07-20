# Web Dashboard API Docs (Clinician / Facility Admin-facing)

API reference for the **Binti Care web dashboard** — used by `CLINICIAN` and `FACILITY_ADMIN` staff. Every endpoint here requires a staff-role access token plus:

```
X-Facility-Context: <facility_id>
```

...the UUID of a facility the caller is an active staff member of. See `docs/shared/conventions.md` for the response envelope/error codes and `docs/shared/auth.md` for login (shared with the mobile app) and how `staff_memberships` drives the facility selector.

## Modules

| Doc | Covers |
|---|---|
| [`facilities.md`](./facilities.md) | Facility self-registration, own-facility management, staff roster, patient assignment |
| [`facility-admin.md`](./facility-admin.md) | Admin dashboard overview, patient directory, bulk reassignment, staff invites/capacity |
| [`clinician-dashboard.md`](./clinician-dashboard.md) | Clinician's personal dashboard — summary, alerts, patient directory/timeline |
| [`medical-history.md`](./medical-history.md) | Recording/updating a patient's medical history, facility custom fields |
| [`pregnancy-clinical.md`](./pregnancy-clinical.md) | Viewing patient vitals, leaving feedback, manual ANC visits, risk-score override |
| [`labour.md`](./labour.md) | Full labour session + partograph + alert management, facility-wide labour feed |
| [`postpartum-clinical.md`](./postpartum-clinical.md) | Viewing a patient's babies/EPDS/check-ins, facility postpartum alert summaries |
| [`referrals.md`](./referrals.md) | Accepting/rejecting/completing referrals, patient summary, inbox |
| [`emergencies.md`](./emergencies.md) | Facility emergency SOS inbox and status updates |
| [`education-management.md`](./education-management.md) | Creating/editing educational content and events |
| [`system-templates.md`](./system-templates.md) | Listing form/care-pathway templates, creating facility-specific form overrides |
| [`reports.md`](./reports.md) | Population snapshot, generating and downloading facility reports |
| [`notifications-system.md`](./notifications-system.md) | Internal SMS send, inbound SMS webhook, live WebSocket alert channel |

## Not in this folder

Anything a mother does from the mobile app — logging her own vitals, creating her own referral, reading education content — lives in `docs/mobile/` instead. Several modules above have a same-named counterpart there covering the patient-facing side of that same feature area.
