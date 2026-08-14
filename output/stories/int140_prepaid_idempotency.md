# INT140 / INT146 – Reference Numbers and Idempotency for Booking Payments

## Splitting Rationale

One Change Request is raised covering both INT140 and INT146. Both are existing MuleSoft interfaces handling Datatrans payment calls, and both require a defined idempotency key strategy to prevent duplicate transactions and correctly handle retries. The change is consolidated because it addresses the same root cause (absence of explicit idempotency key management) across two related payment flows under open point DTTP25-31456.

- INT140 (Prepaid Booking): idempotency keys are scoped to the prebooking number where available, and fall back to the transactionId for cancel calls where the prebooking number is not yet available.
- INT146 (MyMSC Post-Booking Payment): idempotency keys are scoped to the transactionId for all call types, because each payment attempt in MyMSC uses a new transaction and must be distinguishable from prior failed attempts on the same booking.

No ADF interfaces are involved or referenced.

---

## Change Requests

---

Type: CR
Summary: INT140 / INT146 – Define idempotency key strategy for Datatrans payment calls
Jira Ticket: DTTP25-31456
Description:
  Change Scope: Interfaces INT140 (Prepaid Booking) and INT146 (MyMSC Post-Booking Payment) – Datatrans payment calls. MuleSoft changes:

  INT140:
    - For the Datatrans authorize call (POST /v1/transactions/{transactionId}/authorize), set the idempotency key to {PreBkgno}_PREPAID-authorize and the refno to {PreBkgno}_PREPAID. The autoSettle field is set to true, meaning the authorization also settles the transaction for authenticationOnly payment methods. No separate settle call is made in this path.
    - For the Datatrans cancel call triggered before the prebooking number is available (item validation failure, CMS call failure, booking retrieval failure, or booking creation failure), set the idempotency key to {transactionId}-cancel.
    - For the Datatrans settle call (POST /v1/transactions/{transactionId}/settle), triggered after the prepaid booking is successfully created, set the idempotency key to {PreBkgno}_PREPAID-settle and the refno to {PreBkgno}_PREPAID. The currency field must be set to the 3-letter ISO currency code of the transaction currency.
    - For the Datatrans cancel call triggered after the prepaid booking is created but must subsequently be cancelled (transaction amount mismatch, coupon warnings, or settlement failure), set the idempotency key to {transactionId}-cancel. This is consistent with the pre-booking cancel scenario; the two cancel scenarios are mutually exclusive so no conflict is expected.
    - The idempotency key format for cancel calls is subject to clarification in open point DTTP25-38602.
    - Increase the timeout for the Datatrans authorize, settle, and cancel calls to 10 seconds. The timeout for the Datatrans init call can remain at 5 seconds.

  INT146:
    - For the Datatrans authorize call, set the idempotency key to {transactionId}-authorize.
    - For the Datatrans settle call, set the idempotency key to {transactionId}-settle.
    - For the Datatrans cancel call, set the idempotency key to {transactionId}-cancel.
    - Using the transactionId (rather than the booking reference number) ensures that each distinct payment attempt from MyMSC is uniquely identifiable, preventing Datatrans from replaying the response of a previous failed attempt when the customer retries with a different card or a new transaction.
    - Increase the timeout for the Datatrans authorize, settle, and cancel calls to 10 seconds. The timeout for the Datatrans init call can remain at 5 seconds.

  Rationale: In the absence of explicit idempotency key management, Datatrans can replay the response of a previously failed transaction when the same idempotency key is reused across different payment attempts. This was confirmed by testing: a retry on INT146 for booking 067221051 using a new card was incorrectly declined because Datatrans recognised the same reference number and idempotency key from a prior blocked-card attempt and returned the original decline response. Defining a consistent per-call-type key strategy ensures each Datatrans operation is uniquely identifiable, retries within the same call are safe, and distinct payment attempts are correctly processed as independent transactions.

  Resources:
    - Mule Specification Document: [TO BE CONFIRMED]
    - High Level Architecture Document: [TO BE CONFIRMED]
    - API Documentation:
      - IA INT140 – Prepaid Booking: [TO BE CONFIRMED]
      - IA INT146 – MyMSC Post-Booking Payment: [TO BE CONFIRMED]
    - Confluence Page: [TO BE CONFIRMED]
    - Open Point: DTTP25-38602 – [INT140] Use of idempotency key for cancellation of transaction

Acceptance Criteria (BDD):
  Given a prepaid booking flow is initiated and a prebooking number (PreBkgno) has been generated
  When INT140 calls POST /v1/transactions/{transactionId}/authorize on Datatrans
  Then the request is sent with Idempotency-Key: {PreBkgno}_PREPAID-authorize, refno: {PreBkgno}_PREPAID, and autoSettle: true, and the transaction is both authorised and settled in a single call

  Given a prepaid booking flow is initiated and a separate settle step is required (non-authenticationOnly payment method) and the prepaid booking has been successfully created
  When INT140 calls POST /v1/transactions/{transactionId}/settle on Datatrans
  Then the request is sent with Idempotency-Key: {PreBkgno}_PREPAID-settle, refno: {PreBkgno}_PREPAID, and the correct 3-letter ISO currency code

  Given a prepaid booking flow fails before the prebooking number is available (item validation failure, CMS call failure, booking retrieval failure, or booking creation failure) and the Klarna transaction must be cancelled
  When INT140 calls POST /v1/transactions/{transactionId}/cancel on Datatrans
  Then the request is sent with Idempotency-Key: {transactionId}-cancel

  Given a prepaid booking has been created but must subsequently be cancelled due to a transaction amount mismatch, coupon warnings, or settlement failure
  When INT140 calls POST /v1/transactions/{transactionId}/cancel on Datatrans
  Then the request is sent with Idempotency-Key: {transactionId}-cancel, and no idempotency key conflict occurs as the two cancel scenarios are mutually exclusive

  Given a customer in MyMSC initiates a payment for an existing booking and INT146 calls Datatrans to authorize the transaction
  When INT146 sends the authorize request
  Then the request is sent with Idempotency-Key: {transactionId}-authorize

  Given a customer in MyMSC has successfully authorized a payment and INT146 proceeds to settle the transaction
  When INT146 sends the settle request
  Then the request is sent with Idempotency-Key: {transactionId}-settle

  Given a customer in MyMSC previously attempted a payment that failed (e.g. card blocked) and now retries with a new card, resulting in a new transactionId
  When INT146 calls Datatrans to authorize the new transaction
  Then the request is sent with a new Idempotency-Key based on the new transactionId, Datatrans does not replay the response of the previous failed attempt, and the new payment attempt is processed independently
