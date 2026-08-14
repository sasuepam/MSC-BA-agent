# INT113 GetBooking: FormOfPayment PL Value

**Source:** Jira Open Point [DTTP25-38799](https://smartship.atlassian.net/browse/DTTP25-38799) — [MyMSC][INT113][PROD] GetBooking response invalid FormOfPayment field value

## Splitting Rationale

One Change Request is raised for this feature. INT113 is an existing MuleSoft interface, and the open point describes a single targeted change: extend the accepted values for the `FormOfPayment` field in the GetBooking response to include `PL`, which DTS is actively returning in PROD but is not currently listed in the IA. No ADF interfaces are involved or referenced.

| Story | Scope | Reason for separation (or consolidation) |
|---|---|---|
| CR-1: INT113 – Accept PL as valid FormOfPayment in GetBooking response | INT113 – add PL to the accepted FormOfPayment values in the DtsRetrieveBookingResponseMessage response validation. | Single CR: one existing interface, one field validation change, one open point ticket (DTTP25-38799). No independent sub-features or different change types warrant splitting. |

---

## Change Requests

---

Type: CR
Summary: [INT113] Accept PL as valid FormOfPayment in GetBooking response
Jira Ticket: DTTP25-38799
Description:
  Change Scope: Interface INT113 (MyMSC GetBooking). MuleSoft changes:
    - Add `PL` to the list of accepted values for the `FormOfPayment` field in `DtsRetrieveBookingResponseMessage.PreBookings.PreBooking[N].PrePaidPayments[N].PrePaidPayment.FormOfPayment`.
    - Current accepted values per IA: CC, AC, AR, BW, CK, CO, CS, GA, VC, VO.
    - Updated accepted values: CC, AC, AR, BW, CK, CO, CS, GA, VC, VO, PL.
    - The interface must be updated to include PL as a valid FormOfPayment value.
    - All existing INT113 validation and response behaviour for other FormOfPayment values is unchanged.

  Rationale: During PROD load testing, DTS was observed returning `PL` as a FormOfPayment value for pre-paid payments in the GetBooking response. This value was not listed in the IA and is not captured in the current implementation, causing response validation errors in INT113 and breaking booking retrieval for any booking where a pre-paid payment uses PL. The fix aligns the MuleSoft validation with the actual values DTS can return, restoring correct booking retrieval for affected records.

  Resources:
    - Mule Specification Document: [TO BE CONFIRMED]
    - High Level Architecture Document: [TO BE CONFIRMED]
    - API Documentation:
      - IA INT113 – MyMSC GetBooking: [TO BE CONFIRMED]
    - Confluence Page: [TO BE CONFIRMED]

Acceptance Criteria (BDD):
  Given a booking exists in DTS with a pre-paid payment where FormOfPayment = PL
  When INT113 GetBooking is called for that booking
  Then the response is processed without validation errors and FormOfPayment is returned as PL in the response payload

  Given a booking exists in DTS with a pre-paid payment where FormOfPayment is one of the existing accepted values (CC, AC, AR, BW, CK, CO, CS, GA, VC, VO)
  When INT113 GetBooking is called for that booking
  Then the response is processed without validation errors and behaviour is identical to current

  Given a booking has multiple pre-paid payments, one with FormOfPayment = PL and others with existing valid values
  When INT113 GetBooking is called for that booking
  Then all pre-paid payments are returned correctly, no validation error is raised, and all FormOfPayment values appear in the response

  Given DTS returns a FormOfPayment value that is not in the updated accepted list
  When INT113 GetBooking processes the response
  Then a validation error is raised with an appropriate error code and the issue is logged; the invalid value does not silently pass through to the consumer
