# Mobile API Docs (Mother-facing)

API reference for the **Binti Care mobile app** — the mother/patient-facing client. Every endpoint here is called with a `USER`-role access token (occasionally combined with a public/unauthenticated path, called out explicitly where relevant).

Start with **`docs/shared/conventions.md`** for the response envelope, error codes, and base URL, and **`docs/shared/auth.md`** for registration/login (shared with the web dashboard).

## Modules

| Doc | Covers |
|---|---|
| [`profile.md`](./profile.md) | Own profile, QR passport, personal-doctor requests, consent management |
| [`medical-history.md`](./medical-history.md) | Viewing your own medical history record |
| [`facilities.md`](./facilities.md) | Browsing/searching facilities, "nearby" lookup |
| [`cycle-tracking.md`](./cycle-tracking.md) | Period entries, symptoms, predictions, HMB alerts |
| [`pregnancy.md`](./pregnancy.md) | Pregnancy record, vitals logging, ANC visit schedule, risk score, nutrition guidance |
| [`labour.md`](./labour.md) | Read-only labour/birth status view |
| [`postpartum.md`](./postpartum.md) | Maternal check-ins, EPDS depression screening, baby profiles/vitals/milestones/vaccinations |
| [`referrals-emergencies.md`](./referrals-emergencies.md) | Creating referrals/emergency SOS requests, viewing your own |
| [`reminders-notifications.md`](./reminders-notifications.md) | Custom reminders, push device registration, in-app notifications, SMS preference |
| [`education.md`](./education.md) | Reading educational content, events, and the combined feed |
| [`ai-companion.md`](./ai-companion.md) | AI chat companion consent, context summary, real-time chat |

## Not in this folder

Anything that requires a `CLINICIAN`/`FACILITY_ADMIN` role or the `X-Facility-Context` header lives in `docs/web/` instead — e.g. accepting a referral, logging labour readings, managing facility staff, or viewing another patient's records. Several modules above have a same-named counterpart under `docs/web/` covering the clinical/administrative side of that same feature area.
