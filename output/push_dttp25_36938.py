import json, urllib.request, urllib.error, base64, os

JIRA_URL = "https://smartship.atlassian.net"
JIRA_EMAIL = "sarah_suda@epam.com"
JIRA_TOKEN = os.environ.get("JIRA_TOKEN", "")
auth = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_TOKEN}".encode()).decode()

def para(t): return {"type":"paragraph","content":[{"type":"text","text":t}]}
def h(t,l=2): return {"type":"heading","attrs":{"level":l},"content":[{"type":"text","text":t}]}
def bullets(items): return {"type":"bulletList","content":[{"type":"listItem","content":[para(i)]} for i in items]}

description_adf = {"type":"doc","version":1,"content":[
    h("Change Scope"),
    para("Interfaces INT140 (Prepaid Booking) and INT146 (MyMSC Post-Booking Payment) - Datatrans payment calls. MuleSoft changes:"),
    h("INT140", 3),
    bullets([
        "For the Datatrans authorize call (POST /v1/transactions/{transactionId}/authorize), set the idempotency key to {PreBkgno}_PREPAID-authorize and the refno to {PreBkgno}_PREPAID. The autoSettle field is set to true, meaning the authorization also settles the transaction for authenticationOnly payment methods. No separate settle call is made in this path.",
        "For the Datatrans cancel call triggered before the prebooking number is available (item validation failure, CMS call failure, booking retrieval failure, or booking creation failure), set the idempotency key to {transactionId}-cancel.",
        "For the Datatrans settle call (POST /v1/transactions/{transactionId}/settle), triggered after the prepaid booking is successfully created, set the idempotency key to {PreBkgno}_PREPAID-settle and the refno to {PreBkgno}_PREPAID. The currency field must be set to the 3-letter ISO currency code of the transaction currency.",
        "For the Datatrans cancel call triggered after the prepaid booking is created but must subsequently be cancelled (transaction amount mismatch, coupon warnings, or settlement failure), set the idempotency key to {transactionId}-cancel. This is consistent with the pre-booking cancel scenario; the two cancel scenarios are mutually exclusive so no conflict is expected.",
        "The idempotency key format for cancel calls is subject to clarification in open point DTTP25-38602.",
        "Increase the timeout for the Datatrans authorize, settle, and cancel calls to 10 seconds. The timeout for the Datatrans init call can remain at 5 seconds.",
    ]),
    h("INT146", 3),
    bullets([
        "For the Datatrans authorize call, set the idempotency key to {transactionId}-authorize.",
        "For the Datatrans settle call, set the idempotency key to {transactionId}-settle.",
        "For the Datatrans cancel call, set the idempotency key to {transactionId}-cancel.",
        "Using the transactionId (rather than the booking reference number) ensures that each distinct payment attempt from MyMSC is uniquely identifiable, preventing Datatrans from replaying the response of a previous failed attempt when the customer retries with a different card or a new transaction.",
        "Increase the timeout for the Datatrans authorize, settle, and cancel calls to 10 seconds. The timeout for the Datatrans init call can remain at 5 seconds.",
    ]),
    h("Rationale"),
    para("In the absence of explicit idempotency key management, Datatrans can replay the response of a previously failed transaction when the same idempotency key is reused across different payment attempts. This was confirmed by testing: a retry on INT146 for booking 067221051 using a new card was incorrectly declined because Datatrans recognised the same reference number and idempotency key from a prior blocked-card attempt and returned the original decline response. Defining a consistent per-call-type key strategy ensures each Datatrans operation is uniquely identifiable, retries within the same call are safe, and distinct payment attempts are correctly processed as independent transactions. Increasing the timeout to 10 seconds for authorize, settle, and cancel calls reduces the risk of premature timeout errors that could leave the outcome of a Datatrans call unknown and result in the customer being charged twice."),
    h("Resources"),
    bullets([
        "Mule Specification Document: [TO BE CONFIRMED]",
        "High Level Architecture Document: [TO BE CONFIRMED]",
        "API Documentation: IA INT140 - Prepaid Booking: [TO BE CONFIRMED]",
        "API Documentation: IA INT146 - MyMSC Post-Booking Payment: [TO BE CONFIRMED]",
        "Confluence Page: [TO BE CONFIRMED]",
        "Open Point: DTTP25-38602 - [INT140] Use of idempotency key for cancellation of transaction",
    ])
]}

ac_adf = {"type":"doc","version":1,"content":[
    h("Scenario 1 (INT140): Authorize call with autoSettle"),
    para("Given a prepaid booking flow is initiated and a prebooking number (PreBkgno) has been generated"),
    para("When INT140 calls POST /v1/transactions/{transactionId}/authorize on Datatrans"),
    para("Then the request is sent with Idempotency-Key: {PreBkgno}_PREPAID-authorize, refno: {PreBkgno}_PREPAID, and autoSettle: true, and the transaction is both authorised and settled in a single call"),
    h("Scenario 2 (INT140): Settle call after booking creation"),
    para("Given a prepaid booking flow is initiated and a separate settle step is required (non-authenticationOnly payment method) and the prepaid booking has been successfully created"),
    para("When INT140 calls POST /v1/transactions/{transactionId}/settle on Datatrans"),
    para("Then the request is sent with Idempotency-Key: {PreBkgno}_PREPAID-settle, refno: {PreBkgno}_PREPAID, and the correct 3-letter ISO currency code"),
    h("Scenario 3 (INT140): Cancel before prebooking number is available"),
    para("Given a prepaid booking flow fails before the prebooking number is available and the Klarna transaction must be cancelled"),
    para("When INT140 calls POST /v1/transactions/{transactionId}/cancel on Datatrans"),
    para("Then the request is sent with Idempotency-Key: {transactionId}-cancel"),
    h("Scenario 4 (INT140): Cancel after prebooking created"),
    para("Given a prepaid booking has been created but must subsequently be cancelled due to a transaction amount mismatch, coupon warnings, or settlement failure"),
    para("When INT140 calls POST /v1/transactions/{transactionId}/cancel on Datatrans"),
    para("Then the request is sent with Idempotency-Key: {transactionId}-cancel, and no idempotency key conflict occurs as the two cancel scenarios are mutually exclusive"),
    h("Scenario 5 (INT146): Authorize call"),
    para("Given a customer in MyMSC initiates a payment for an existing booking and INT146 calls Datatrans to authorize the transaction"),
    para("When INT146 sends the authorize request"),
    para("Then the request is sent with Idempotency-Key: {transactionId}-authorize"),
    h("Scenario 6 (INT146): Settle call"),
    para("Given a customer in MyMSC has successfully authorized a payment and INT146 proceeds to settle the transaction"),
    para("When INT146 sends the settle request"),
    para("Then the request is sent with Idempotency-Key: {transactionId}-settle"),
    h("Scenario 7 (INT146): Retry with new card produces independent transaction"),
    para("Given a customer in MyMSC previously attempted a payment that failed (e.g. card blocked) and now retries with a new card, resulting in a new transactionId"),
    para("When INT146 calls Datatrans to authorize the new transaction"),
    para("Then the request is sent with a new Idempotency-Key based on the new transactionId, Datatrans does not replay the response of the previous failed attempt, and the new payment attempt is processed independently"),
    h("Scenario 8 (INT140 / INT146): Datatrans call completes within extended timeout"),
    para("Given INT140 or INT146 sends an authorize, settle, or cancel call to Datatrans"),
    para("When Datatrans responds within 10 seconds"),
    para("Then the response is processed successfully and no timeout error is raised"),
]}

payload = {"fields":{"description":description_adf,"customfield_11506":ac_adf}}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    f"{JIRA_URL}/rest/api/3/issue/DTTP25-36938",
    data=data, method="PUT",
    headers={"Authorization":f"Basic {auth}","Content-Type":"application/json","Accept":"application/json"}
)
try:
    with urllib.request.urlopen(req) as resp:
        print(f"SUCCESS: {resp.status}")
except urllib.error.HTTPError as e:
    print(f"ERROR {e.code}: {e.read().decode()}")
