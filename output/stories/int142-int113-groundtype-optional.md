# INT142/INT113 GetBooking: GroundType Field Optional

**Source:** Jira Open Point [DTTP25-38826](https://smartship.atlassian.net/browse/DTTP25-38826) — [PROD][MyMSC][INT142/113] Get booking details invalid GroundType value

## Splitting Rationale

One Change Request is raised for this feature. INT142 and INT113 are both existing MuleSoft interfaces affected by the same change: the `GroundType` field is currently marked as mandatory in the IA but DTS can return it as absent or empty for certain bookings. Per splitting rules, the same change across multiple interfaces is consolidated into a single CR. No ADF interfaces are involved or referenced.

| Story | Scope | Reason for separation (or consolidation) |
|---|---|---|
| CR-1: INT142/INT113 – Handle missing GroundType field in GetBooking response | INT142 and INT113 – make GroundType optional in the IA and update MuleSoft response validation to accept absent or empty values. | Single CR: same field validation change across two existing interfaces. Same logical fix, same root cause. |

---

## Change Requests

---

Type: CR
Summary: [INT142/INT113] Handle missing GroundType field in GetBooking response
Jira Ticket: DTTP25-38826
Description:
  Change Scope: Interfaces INT142 and INT113 (MyMSC GetBooking). MuleSoft changes:
    - Update response validation in INT142 and INT113 to accept absent or empty values for the `GroundType` field in `DtsRetrieveBookingResponseMessage.PreBookings.PreBooking[N].ItemInfo[n].ActivityMoreInfo.GroundType`.
    - The IA currently marks this field as mandatory; the IA must be aligned to reflect that `GroundType` is optional and may be absent for certain booking types.
    - When `GroundType` is absent or empty, the interface must process the response without raising a validation error.
    - All other mandatory field validations in the response are unchanged.

  Rationale: During PROD load testing, DTS was observed returning GetBooking responses where the `GroundType` field was absent or empty for certain bookings (e.g. booking 68891320). This value was not accounted for in the current IA and is not captured in the current implementation, causing validation errors in INT142 and INT113 when processing affected bookings. The fix aligns the IA and MuleSoft validation with the actual DTS behaviour, preventing failures for bookings where `GroundType` is not applicable or not populated by the source system.

  Resources:
    - Mule Specification Document: [TO BE CONFIRMED]
    - High Level Architecture Document: [TO BE CONFIRMED]
    - API Documentation:
      - IA INT142 – MyMSC GetBooking: [TO BE CONFIRMED]
      - IA INT113 – MyMSC GetBooking: [TO BE CONFIRMED]

Acceptance Criteria (BDD):
  Given a booking exists in DTS where the ActivityMoreInfo block is present and GroundType is populated
  When INT142 or INT113 GetBooking is called for that booking
  Then the response is processed without validation errors and GroundType is returned with its value in the response payload

  Given a booking exists in DTS where the ActivityMoreInfo block is present but GroundType is absent or empty
  When INT142 or INT113 GetBooking is called for that booking
  Then the response is processed without validation errors and the absence of GroundType does not cause a failure

  Given a booking exists in DTS where the ActivityMoreInfo block is absent entirely
  When INT142 or INT113 GetBooking is called for that booking
  Then the response is processed without validation errors and no GroundType validation is triggered

  Given a booking response from DTS is missing a field that remains truly mandatory in the IA
  When INT142 or INT113 GetBooking processes the response
  Then a validation error is raised with an appropriate error code and the issue is logged; mandatory field validation is not weakened by this change
