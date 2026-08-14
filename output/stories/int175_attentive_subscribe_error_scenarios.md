Type: CR
Summary: INT175 Attentive Subscribe – Introduce error scenario handling
Description:
  Change Scope: INT175 (Attentive Subscription API — MuleSoft calls Attentive to subscribe a customer to marketing communications) must be updated to handle all Attentive error response codes. The change applies at the experience API level and introduces three categories of error behaviour:

  Specific errors (HTTP 400 with original Attentive error code):
  These errors contain meaningful, actionable information and are surfaced directly to the caller:
  - INVALID_DESTINATION: the destination information is missing or invalid — phone number, email address, or destination type is incorrectly formatted or incomplete
  - COMPANY_REGION_NOT_SUPPORTED: the phone number belongs to a country or region not currently enabled for this Attentive account — the data is valid but the region is unsupported
  - ALREADY_SUBSCRIBED: the user is already subscribed to the requested messaging channel and subscription type (noted as borderline success — kept as error for now)
  - PHONE_INVALID_NUMBER_FOR_REGION: the phone number is not recognised as valid for any of the account's configured SMS regions — area code does not exist, incorrect length, or reserved/non-geographic code
  - PHONE_DOES_NOT_MATCH_ANY_COMPANY_REGION: the phone number is valid but does not belong to any country or region enabled on the Attentive account

  Generic errors (HTTP 400 with generic message "unable to complete subscription"):
  These errors must be masked to avoid exposing suppression status, privacy flags, or internal Attentive risk signals to the caller:
  - USER_SUPPRESSED: the user is currently suppressed in Attentive
  - SUPPRESSED: the destination should not receive messages based on suppression rules or deliverability protections
  - LITIGIOUS: the destination has been identified as high-risk and is not eligible to receive messages
  - TERMINATED: the user's data or subscription record has been terminated due to a deletion or privacy-related request
  - SUSPENDED: the subscription is currently suspended and not eligible for reactivation

  Unhandled errors (HTTP 500):
  These indicate an internal Attentive failure rather than a business rule violation:
  - UNKNOWN: the request could not be processed due to an unspecified error — implies Attentive is broken
  - Any other error code returned by Attentive not covered by the specific or generic categories above

  Rationale: INT175 currently does not have a defined error handling strategy for the full range of Attentive error codes. Without this change, the MuleSoft integration may leak suppression status or privacy-sensitive error details to the caller, or fail to distinguish user-correctable errors from unrecoverable Attentive failures.

  Resources:
    - MuleSoft Requirements Page: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4825547214/IA+INT175+-+Unkown+Subscription
    - High Level Architecture Document: [TO BE CONFIRMED]
    - API Documentation: [TO BE CONFIRMED]

Acceptance Criteria (BDD):
  Scenario: INVALID_DESTINATION – specific error surfaced to caller
  Given Attentive returns HTTP 400 with error code INVALID_DESTINATION (the destination information — phone number, email address, or destination type — is missing, incorrectly formatted, or incomplete)
  When INT175 receives the error response from Attentive
  Then INT175 returns HTTP 400 to the caller with error code INVALID_DESTINATION and the Attentive-provided error message; no generic masking is applied

  Scenario: COMPANY_REGION_NOT_SUPPORTED – specific error surfaced to caller
  Given Attentive returns HTTP 400 with error code COMPANY_REGION_NOT_SUPPORTED (the phone number belongs to a country or region not currently enabled for this Attentive account)
  When INT175 receives the error response from Attentive
  Then INT175 returns HTTP 400 to the caller with error code COMPANY_REGION_NOT_SUPPORTED and the Attentive-provided error message; no generic masking is applied

  Scenario: ALREADY_SUBSCRIBED – specific error surfaced to caller
  Given Attentive returns HTTP 400 with error code ALREADY_SUBSCRIBED (the user is already subscribed to the requested messaging channel and subscription type)
  When INT175 receives the error response from Attentive
  Then INT175 returns HTTP 400 to the caller with error code ALREADY_SUBSCRIBED and the Attentive-provided error message

  Scenario: PHONE_INVALID_NUMBER_FOR_REGION – specific error surfaced to caller
  Given Attentive returns HTTP 400 with error code PHONE_INVALID_NUMBER_FOR_REGION (the phone number is not recognised as valid for any configured SMS region — area code does not exist, incorrect length, or reserved/non-geographic code)
  When INT175 receives the error response from Attentive
  Then INT175 returns HTTP 400 to the caller with error code PHONE_INVALID_NUMBER_FOR_REGION and the Attentive-provided error message; no generic masking is applied

  Scenario: PHONE_DOES_NOT_MATCH_ANY_COMPANY_REGION – specific error surfaced to caller
  Given Attentive returns HTTP 400 with error code PHONE_DOES_NOT_MATCH_ANY_COMPANY_REGION (the phone number is valid but does not belong to any country or region enabled on the Attentive account)
  When INT175 receives the error response from Attentive
  Then INT175 returns HTTP 400 to the caller with error code PHONE_DOES_NOT_MATCH_ANY_COMPANY_REGION and the Attentive-provided error message; no generic masking is applied

  Scenario: USER_SUPPRESSED – masked with generic error
  Given Attentive returns HTTP 400 with error code USER_SUPPRESSED (the user is currently suppressed in Attentive)
  When INT175 receives the error response from Attentive
  Then INT175 returns HTTP 400 to the caller with a generic error message "unable to complete subscription"; the USER_SUPPRESSED error code is NOT included in the response to the caller

  Scenario: SUPPRESSED – masked with generic error
  Given Attentive returns HTTP 400 with error code SUPPRESSED (the destination should not receive messages based on suppression rules or deliverability protections)
  When INT175 receives the error response from Attentive
  Then INT175 returns HTTP 400 to the caller with a generic error message "unable to complete subscription"; the SUPPRESSED error code is NOT included in the response to the caller

  Scenario: LITIGIOUS – masked with generic error
  Given Attentive returns HTTP 400 with error code LITIGIOUS (the destination has been identified as high-risk and is not eligible to receive messages)
  When INT175 receives the error response from Attentive
  Then INT175 returns HTTP 400 to the caller with a generic error message "unable to complete subscription"; the LITIGIOUS error code is NOT included in the response to the caller

  Scenario: TERMINATED – masked with generic error
  Given Attentive returns HTTP 400 with error code TERMINATED (the user's data or subscription record has been terminated due to a deletion or privacy-related request)
  When INT175 receives the error response from Attentive
  Then INT175 returns HTTP 400 to the caller with a generic error message "unable to complete subscription"; the TERMINATED error code is NOT included in the response to the caller

  Scenario: SUSPENDED – masked with generic error
  Given Attentive returns HTTP 400 with error code SUSPENDED (the subscription is currently suspended and not eligible for reactivation)
  When INT175 receives the error response from Attentive
  Then INT175 returns HTTP 400 to the caller with a generic error message "unable to complete subscription"; the SUSPENDED error code is NOT included in the response to the caller

  Scenario: UNKNOWN – returned as HTTP 500
  Given Attentive returns an error with code UNKNOWN (the request could not be processed due to an unspecified internal Attentive error — implies Attentive is broken)
  When INT175 receives the UNKNOWN error response from Attentive
  Then INT175 returns HTTP 500 to the caller; this is treated as an unhandled internal error, not a 400-level client error

  Scenario: Unrecognised Attentive error code – returned as HTTP 500
  Given Attentive returns any error code not listed in the specific or generic categories above
  When INT175 receives the unrecognised error response from Attentive
  Then INT175 returns HTTP 500 to the caller; unhandled error codes must not be silently swallowed or forwarded as 400s
