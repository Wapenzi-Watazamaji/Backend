# Binti Care Backend — 20-Day Accelerated Workplan
## Phase 1: Foundation & Data Modeling (Days 1–4)
**Goal:** Complete the entire database schema and authentication layer. Do not start writing routers until the models and relationships are solid.

*   **Ephy (Auth & Entities):**
    *   **Day 1-2:** Build SQLAlchemy models: `User`, `Profile`, `Facility`, `StaffMember`.
    *   **Day 3-4:** Implement JWT Auth (`register`, `login`, `refresh`), Role-Based Access Control (RBAC), and `X-Facility-Context` validation.
*   **Lewis (The Core Engines):**
    *   **Day 1-2:** Build SQLAlchemy models: `FormTemplate`, `FormSubmission`, `CarePathwayTemplate`, `ScheduledVisit`.
    *   **Day 3-4:** Build the Dynamic Form validation engine (validating JSON against schemas) and the Care Pathway instantiation service (auto-generating visits based on triggers).

---

## Phase 2: Core Patient Journeys / Mobile API (Days 5–8)
**Goal:** Flesh out the mother's tracking modules using the engines from Phase 1.

*   **Ephy (Pregnancy):**
    *   **Day 5-6:** Build the Pregnancy endpoints (starts, completions) and vitals submission endpoints.
    *   **Day 7-8:** Implement the Risk Score calculation engine (analyzing recent vitals to flag "High Risk").
*   **Lewis (Cycle & Postpartum):**
    *   **Day 5-6:** Build Cycle Tracking logic (predicting next menses, computing PBAC scores for Heavy Menstrual Bleeding).
    *   **Day 7-8:** Build Postpartum flow (Baby profiles) and the EPDS Depression Screening logic (specifically catching the "self-harm" Q10 flag).

---

## Phase 3: Labour Monitor & Alerts / Web API (Days 9–12)
**Goal:** Build the most critical clinical features for the facility dashboard.

*   **Ephy (The WHO Partograph):**
    *   **Day 9-10:** Model `LabourSession` and `LabourReading`. Build the CRUD endpoints for clinicians to log dilations and fetal heart rates.
    *   **Day 11-12:** Build the Partograph computation logic (detecting when a mother crosses the Alert Line or Action Line).
*   **Lewis (Global Alerts):**
    *   **Day 9-10:** Build the centralized Alerts Dashboard logic (fetching flagged forms + labour alerts + depression flags).
    *   **Day 11-12:** Build the clinician-to-mother Feedback thread API.

---

## Phase 4: Universal Referral Network (Days 13–16)
**Goal:** Connect the facilities together and allow emergency data sharing.

*   **Ephy (Facility Operations):**
    *   **Day 13-14:** Build bulk Patient Assignment and Staff capacity endpoints.
    *   **Day 15-16:** Implement the QR Passport / Consent-gated token system for emergency lookups.
*   **Lewis (Referrals):**
    *   **Day 13-14:** Build `GET /api/facilities/nearby` (using basic haversine distance or PostGIS if available).
    *   **Day 15-16:** Implement the complete Referral lifecycle state machine (Draft -> Sent -> Accepted/Rejected -> Completed).

---

## Phase 5: AI & Final Polish (Days 17–20)
**Goal:** Integrate third-party services and finalize the "wow" features.

*   **Ephy (AI Assistant):**
    *   **Day 17-18:** Integrate the LLM (OpenAI/Anthropic/Gemini) for the Assistant Chat, dynamically injecting the mother's recent vitals as context.
    *   **Day 19-20:** Build the Personalized Education Feed generator.
*   **Lewis (Notifications):**
    *   **Day 17-18:** Integrate an SMS Webhook (e.g., Africa's Talking) for emergency alerts and appointment reminders.
    *   **Day 19-20:** End-to-end testing, bug fixing, and finalizing the Swagger UI documentation.

---

### Pro-Tips for the 20-Day Sprint:
1. **Use AI for Boilerplate:** Have your AI generate all Pydantic schemas based on your SQLAlchemy models.
2. **Mock Third Parties:** Until Day 17, completely mock the AI and SMS systems so you aren't blocked on API keys or network latency.
3. **Daily Syncs:** You and Lewis should sync for 10 minutes every morning to ensure you aren't duplicating API responses.
