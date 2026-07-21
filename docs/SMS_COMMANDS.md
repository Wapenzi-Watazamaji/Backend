# BintiCare SMS Commands Guide

This document outlines all the currently supported SMS commands (intents) that patients can send to the BintiCare Africa's Talking number. These enable patients without smartphones to interact seamlessly with the system.

> **Instant Acknowledgments:** Commands that involve heavy processing (VITALS, STATUS, REQUEST DOCTOR, HELP) send an immediate "processing" SMS so the patient isn't left waiting in silence. The actual result follows as a second message.

## 1. Vitals Logging
**Command:** `VITALS <bp> <weight>`
**Example:** `VITALS 120/80 65`
**Description:** Allows pregnant patients to remotely log their blood pressure (systolic/diastolic) and weight. The data is automatically saved to their active pregnancy record and visible to their clinician.

## 2. Pregnancy Status
**Command:** `STATUS`
**Example:** `STATUS`
**Description:** Returns a snapshot of the patient's current pregnancy including: week number, trimester, due date, days remaining, risk level, and assigned doctor name.

## 3. Next Visit
**Command:** `NEXT VISIT`
**Example:** `NEXT VISIT`
**Description:** Shows the patient's next upcoming scheduled ANC visit, including the date, purpose, and facility name. If no visits are scheduled, advises them to contact their facility.

## 4. My Doctor
**Command:** `MY DOCTOR`
**Example:** `MY DOCTOR`
**Description:** Returns the assigned doctor's name, phone number, and facility. Useful in situations where the patient needs to call their doctor directly. If no doctor is assigned, prompts them to use `REQUEST DOCTOR`.

## 5. Facility Search (Listing)
**Command:** `GET FACILITIES [county_name]`
**Example:** `GET FACILITIES Nairobi`
**Description:** Returns a list of up to 5 verified health facilities. If a county name is provided, it filters the search to that specific county.

## 6. Facility Details
**Command:** `GET FACILITY <facility_name_or_id>`
**Example:** `GET FACILITY Pumwani`
**Description:** Fetches the detailed profile of a specific facility, including its name, county, contact phone number, and the medical services it offers.

## 7. Facility Registration
**Command:** `REGISTER FACILITY <facility_name_or_id>`
**Example:** `REGISTER FACILITY Nairobi Hospital`
**Description:** Registers the patient to their preferred facility. This is required before they can request a personal doctor.

## 8. Requesting a Clinician
**Command:** `REQUEST DOCTOR`
**Example:** `REQUEST DOCTOR`
**Description:** Requests assignment of a personal clinician from the facility the patient is currently registered to. If an active clinician is available, they are assigned immediately, and both the patient and clinician receive an alert. If no clinician is available, the request is marked as pending.

## 9. Emergency Panic Button
**Command:** `HELP` | `EMERGENCY` | `DANGER` | `SOS`
**Example:** `HELP`
**Description:** Triggers an immediate SOS alert. It creates an `EmergencyRequest` tied to their facility, alerts their assigned clinician via an in-app notification, and advises the patient to head to the hospital.

## 10. Facility Events
**Command:** `EVENTS`
**Example:** `EVENTS`
**Description:** Returns up to 3 upcoming education events (e.g., antenatal classes, health talks) at the patient's registered facility, including event title and date/time.

## 11. Educational & Helper Menus
**Command:** `MENU` | `INFO`
**Description:** Returns a numbered menu of all available SMS commands so patients know what they can do.

**Command:** `TIPS`
**Description:** Returns a quick, encouraging pregnancy health tip (e.g., regarding nutrition or rest).

## 12. Unrecognized Commands
**Command:** *(Any text that doesn't match a known intent)*
**Description:** If a patient sends a message that doesn't match any supported command, they receive a friendly reply listing the most commonly used commands and suggesting they reply `MENU` for the full list.

## 13. Check-in Replies (Catch-All)
**Command:** *(Any free text in response to a reminder)*
**Description:** If a patient receives an automated reminder or check-in message, they can simply reply to it. The system will automatically map their reply to the corresponding form submission (e.g., Cycle Tracking or Maternal Check-in) and mark the reminder as completed.

> **Note on Africa's Talking `linkId`:** AT sends a `linkId` with every inbound SMS — this is their internal tracking ID and is **not** used as a BintiCare reminder ID. The `linkedReminderId` field in the webhook schema is reserved for our own reminder linking mechanism.
