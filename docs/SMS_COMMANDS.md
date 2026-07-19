# BintiCare SMS Commands Guide

This document outlines all the currently supported SMS commands (intents) that patients can send to the BintiCare Africa's Talking number. These enable patients without smartphones to interact seamlessly with the system.

## 1. Vitals Logging
**Command:** `VITALS <bp> <weight>`
**Example:** `VITALS 120/80 65`
**Description:** Allows pregnant patients to remotely log their blood pressure (systolic/diastolic) and weight. The data is automatically saved to their active pregnancy record and visible to their clinician.

## 2. Facility Search (Listing)
**Command:** `GET FACILITIES [county_name]`
**Example:** `GET FACILITIES Nairobi`
**Description:** Returns a list of up to 5 verified health facilities. If a county name is provided, it filters the search to that specific county.

## 3. Facility Details
**Command:** `GET FACILITY <facility_name_or_id>`
**Example:** `GET FACILITY Pumwani`
**Description:** Fetches the detailed profile of a specific facility, including its name, county, contact phone number, and the medical services it offers.

## 4. Facility Registration
**Command:** `REGISTER FACILITY <facility_name_or_id>`
**Example:** `REGISTER FACILITY Nairobi Hospital`
**Description:** Registers the patient to their preferred facility. This is required before they can request a personal doctor.

## 5. Requesting a Clinician
**Command:** `REQUEST DOCTOR`
**Example:** `REQUEST DOCTOR`
**Description:** Requests assignment of a personal clinician from the facility the patient is currently registered to. If an active clinician is available, they are assigned immediately, and both the patient and clinician receive an alert.

## 6. Emergency Panic Button
**Command:** `HELP` | `EMERGENCY` | `DANGER` | `SOS`
**Example:** `HELP`
**Description:** Triggers an immediate SOS alert. It creates an `EmergencyRequest` tied to their facility, alerts their assigned clinician via an in-app notification, and advises the patient to head to the hospital.

## 7. Educational & Helper Menus
**Command:** `MENU` | `INFO`
**Description:** Returns a brief menu of the most important SMS commands so patients know what they can do.

**Command:** `TIPS`
**Description:** Returns a quick, encouraging pregnancy health tip (e.g., regarding nutrition or rest).

## 8. Check-in Replies (Catch-All)
**Command:** *(Any free text in response to a reminder)*
**Description:** If a patient receives an automated reminder or check-in message, they can simply reply to it. The system will automatically map their reply to the corresponding form submission (e.g., Cycle Tracking or Maternal Check-in) and mark the reminder as completed.
