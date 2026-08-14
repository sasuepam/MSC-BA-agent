# INT025 BK_PAX_CHANGE_EVENT Ingestion Logic

## Splitting Rationale

One Change Request is raised for this feature. INT025 is an existing MuleSoft interface, and the specification describes a single, cohesive logical change to its ingestion logic: restrict BK_PAX_CHANGE_EVENT propagation from all passengers on a booking to only those flagged with `isChanged=true`, forwarding one event per booking-cruise-passenger combination for each cruise segment the changed passenger appears on.

All business requirements and use cases in the spec relate to this one change. No ADF interfaces are involved or referenced.

| Story | Scope | Reason for separation (or consolidation) |
|---|---|---|
| CR-1: INT025 – Restrict BK_PAX_CHANGE_EVENT to changed passengers only | INT025 – filter incoming BK_PAX_CHANGE_EVENT by `isChanged=true`, fan out one event per booking-cruise-passenger combination per cruise segment. | Single CR: one existing interface, one logical change, one open point ticket (CRM2-10010). No independent sub-features or different change types warrant splitting. |

---

## Change Requests

---

Type: CR
Summary: INT025 – Restrict BK_PAX_CHANGE_EVENT propagation to changed passengers only
Jira Ticket: CRM2-10010
Description:
  Change Scope: Interface INT025 (DTS Booking Event Orchestration → AJO). MuleSoft changes:
    - Inspect the `isChanged` flag on each participant in the incoming BK_PAX_CHANGE_EVENT payload from DTS.
    - Forward the event to AJO only for passengers where `isChanged=true`; passengers where the flag is absent or `false` must be excluded from propagation.
    - For each changed passenger, iterate over all cruise segments in the booking and forward one event per booking-cruise-passenger combination (e.g. B1_C1_P1, B1_C2_P1) for every cruise segment that contains that passenger.
    - Cruise segments that contain no changed passenger must not receive any event.
    - All existing INT025 orchestration behaviour for other event types is unchanged.

  Rationale: The current INT025 implementation propagates BK_PAX_CHANGE_EVENT to AJO for all passengers on a booking when any single passenger change is detected. This causes AJO to reset the contact plan (marketing journey) for passengers whose details have not actually changed. Restricting propagation to only the passenger(s) flagged with `isChanged=true` ensures that AJO contact plan resets are triggered exclusively for the affected individual, preventing unintended disruption to the marketing journeys of other passengers on the same booking. The per-cruise-segment fan-out ensures the reset is applied consistently across all itineraries the changed passenger is booked on. This change resolves open point CRM2-10010 and supports all field-level change types defined in parent requirement CRM2-9923 (first name, last name, date of birth, email, mobile, language, biometric check-in completion, credit card registration).

  Resources:
    - Mule Specification Document: [TO BE CONFIRMED]
    - High Level Architecture Document: [TO BE CONFIRMED]
    - API Documentation:
      - IA INT025 – Booking Event Orchestration: [TO BE CONFIRMED]
    - Confluence Page: [TO BE CONFIRMED]

Acceptance Criteria (BDD):
  Given DTS sends a BK_PAX_CHANGE_EVENT for booking B1 with passengers P1 (isChanged=true), P2 (isChanged=false), and P3 (isChanged=false), and the booking contains cruise segment C1 referencing P1 and P2, and cruise segment C2 referencing P1 and P3
  When INT025 processes the event
  Then INT025 forwards the event to AJO for B1_C1_P1 and B1_C2_P1 only, AJO does not receive any event for P2 or P3 in any combination, INT025 returns a successful response to DTS, and a log entry confirms P1 was identified as changed and events were forwarded for B1_C1_P1 and B1_C2_P1

  Given DTS sends a BK_PAX_CHANGE_EVENT for booking B1 with P1 (isChanged=true) and P2 (isChanged=false), and the booking contains cruise segment C1 referencing P1 and P2, and cruise segment C2 referencing P2 only
  When INT025 processes the event
  Then INT025 forwards exactly one event to AJO for B1_C1_P1, AJO does not receive any event for B1_C2 or for P2 in any segment, INT025 returns a successful response to DTS, and a log entry confirms P1 was found in C1 only and one event was forwarded

  Given DTS sends a BK_PAX_CHANGE_EVENT for booking B1 with P1 (isChanged=true) and P2 (isChanged=true), and the booking contains cruise segment C1 referencing P1 and P2, and cruise segment C2 referencing P1 only
  When INT025 processes the event
  Then INT025 forwards exactly three events to AJO: B1_C1_P1, B1_C2_P1, and B1_C1_P2, AJO does not receive an event for B1_C2_P2 because P2 does not appear in C2, and a log entry confirms both P1 and P2 were identified as changed and lists all forwarded combinations

