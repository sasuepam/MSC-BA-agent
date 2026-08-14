# INT137 – Idempotency Key for Prepaid Item Refunds

## Splitting Rationale

One Change Request is raised for this feature. INT137 (MyMSC Refund Item) is an existing MuleSoft interface. The change is limited to setting an explicit idempotency key on the Datatrans credit (refund) API call to prevent duplicate refunds being issued to the customer for the same item within the Datatrans 60-minute idempotency window. The agreed approach is to use the prebooking number combined with the item ID as the idempotency key.

Datatrans timeout handling for the refund call is out of scope for this CR and is pending a separate decision.

No ADF interfaces are involved or referenced.

---

## Change Requests

---

Type: CR
Summary: INT137 – Set idempotency key on Datatrans refund call to prevent duplicate refunds
Jira Ticket: DTTP25-35473
Description:
  Change Scope: Interface INT137v2 (MyMSC Refund Item – Datatrans credit call). MuleSoft changes:
    - For each Datatrans refund (credit) call made during prepaid item refund processing, set the Idempotency-Key request header to {prebookingnumber}_{itemid}.
    - The prebooking number identifies the prepaid booking associated with the item, and the item ID identifies the specific item being refunded, ensuring the key is unique per item per booking.
    - Where a refund is created for multiple items across one or more prepaid bookings (one refund call per item per passenger), each call must use its own distinct idempotency key constructed from the corresponding prebooking number and item ID.
    - Within the Datatrans 60-minute idempotency window, any retry of the refund call using the same idempotency key will return the result of the original request without creating a new refund transaction, preventing the customer from being refunded twice for the same item.
    - Note: the 60-minute idempotency window is a Datatrans platform constraint. Retries initiated more than 60 minutes after the original call fall outside this protection and are not covered by this change.

  Rationale: When refunding an onboard service or excursion for selected passengers, INT137v2 creates one Datatrans refund transaction per item. If a refund call times out or returns an indeterminate result, the current design KOs the item refund on DTS and returns the item to BKD status, allowing the customer to initiate another refund request. Without an idempotency key, this retry would create a second Datatrans refund transaction for the same item and the customer could be refunded twice. Setting the idempotency key to {prebookingnumber}_{itemid} ensures that within 60 minutes, any retry of the same refund call returns the original Datatrans response rather than creating a duplicate transaction.

  Resources:
    - Mule Specification Document: [TO BE CONFIRMED]
    - High Level Architecture Document: [TO BE CONFIRMED]
    - API Documentation:
      - IA INT137v2 – MyMSC Refund Item: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4166975795/INT137V2+-+MyMSC+Refund+item
      - Datatrans Credit API: https://api-reference.datatrans.ch/#tag/v1transactions/operation/credit
      - Datatrans Idempotency: https://api-reference.datatrans.ch/#section/Idempotency
    - Confluence Page: [TO BE CONFIRMED]
    - Open Point: DTTP25-35473 – [MyMSC] [INT137] Idempotency of prepaid item refunds and handling of Datatrans timeouts

Acceptance Criteria (BDD):
  Given a customer requests a refund for a prepaid item and INT137v2 calls the Datatrans credit endpoint for that item
  When INT137v2 sends the refund request
  Then the request includes the Idempotency-Key header set to {prebookingnumber}_{itemid}, where prebookingnumber is the prepaid booking number associated with the item and itemid is the unique identifier of the item being refunded

  Given a refund is being processed for multiple items across one or more prepaid bookings
  When INT137v2 sends a Datatrans credit call for each item
  Then each call is sent with a distinct Idempotency-Key constructed from the corresponding prebooking number and item ID, and no two items share the same idempotency key

  Given INT137v2 has already submitted a Datatrans refund call for a given item and the same call is retried within 60 minutes using the same idempotency key
  When Datatrans receives the retry request
  Then Datatrans returns the result of the original request without creating a new refund transaction, preventing the customer from being refunded twice for the same item

  Given INT137v2 submits a Datatrans refund call for a given item and Datatrans returns a clear error response (e.g. SERVER_ERROR)
  When INT137v2 processes the error
  Then the item refund is KO'd on DTS and the item is returned to BKD status, and a retry within 60 minutes using the same idempotency key will return the same error from Datatrans
