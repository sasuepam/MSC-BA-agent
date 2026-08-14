import json, urllib.request, urllib.error, base64, os

JIRA_URL = "https://smartship.atlassian.net"
JIRA_EMAIL = "sarah_suda@epam.com"
JIRA_TOKEN = os.environ.get("JIRA_TOKEN", "")
auth = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_TOKEN}".encode()).decode()

def para(t): return {"type":"paragraph","content":[{"type":"text","text":t}]}
def h(t,l=2): return {"type":"heading","attrs":{"level":l},"content":[{"type":"text","text":t}]}
def bullets(items): return {"type":"bulletList","content":[{"type":"listItem","content":[para(i)]} for i in items]}
def link(text, url): return {"type":"paragraph","content":[{"type":"text","text":text+" "},{"type":"text","text":url,"marks":[{"type":"link","attrs":{"href":url}}]}]}

description_adf = {"type":"doc","version":1,"content":[
    h("Change Scope"),
    para("Interface INT137v2 (MyMSC Refund Item - Datatrans credit call). MuleSoft changes:"),
    bullets([
        "For each Datatrans refund (credit) call made during prepaid item refund processing, set the Idempotency-Key request header to {prebookingnumber}_{itemid}.",
        "The prebooking number identifies the prepaid booking associated with the item, and the item ID identifies the specific item being refunded, ensuring the key is unique per item per booking.",
        "Where a refund is created for multiple items across one or more prepaid bookings (one refund call per item per passenger), each call must use its own distinct idempotency key constructed from the corresponding prebooking number and item ID.",
        "Within the Datatrans 60-minute idempotency window, any retry of the refund call using the same idempotency key will return the result of the original request without creating a new refund transaction, preventing the customer from being refunded twice for the same item.",
        "Note: the 60-minute idempotency window is a Datatrans platform constraint. Retries initiated more than 60 minutes after the original call fall outside this protection and are not covered by this change.",
    ]),
    h("Rationale"),
    para("When refunding an onboard service or excursion for selected passengers, INT137v2 creates one Datatrans refund transaction per item. If a refund call times out or returns an indeterminate result, the current design KOs the item refund on DTS and returns the item to BKD status, allowing the customer to initiate another refund request. Without an idempotency key, this retry would create a second Datatrans refund transaction for the same item and the customer could be refunded twice. Setting the idempotency key to {prebookingnumber}_{itemid} ensures that within 60 minutes, any retry of the same refund call returns the original Datatrans response rather than creating a duplicate transaction."),
    h("Resources"),
    bullets([
        "Mule Specification Document: [TO BE CONFIRMED]",
        "High Level Architecture Document: [TO BE CONFIRMED]",
        "API Documentation: IA INT137v2 - MyMSC Refund Item: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4166975795/INT137V2+-+MyMSC+Refund+item",
        "API Documentation: Datatrans Credit API: https://api-reference.datatrans.ch/#tag/v1transactions/operation/credit",
        "API Documentation: Datatrans Idempotency: https://api-reference.datatrans.ch/#section/Idempotency",
        "Confluence Page: [TO BE CONFIRMED]",
        "Open Point: DTTP25-35473 - [MyMSC] [INT137] Idempotency of prepaid item refunds and handling of Datatrans timeouts",
    ])
]}

ac_adf = {"type":"doc","version":1,"content":[
    h("Scenario 1: Refund call includes correct idempotency key"),
    para("Given a customer requests a refund for a prepaid item and INT137v2 calls the Datatrans credit endpoint for that item"),
    para("When INT137v2 sends the refund request"),
    para("Then the request includes the Idempotency-Key header set to {prebookingnumber}_{itemid}, where prebookingnumber is the prepaid booking number associated with the item and itemid is the unique identifier of the item being refunded"),
    h("Scenario 2: Multi-item refund uses distinct key per item"),
    para("Given a refund is being processed for multiple items across one or more prepaid bookings"),
    para("When INT137v2 sends a Datatrans credit call for each item"),
    para("Then each call is sent with a distinct Idempotency-Key constructed from the corresponding prebooking number and item ID, and no two items share the same idempotency key"),
    h("Scenario 3: Retry within 60 minutes does not create duplicate refund"),
    para("Given INT137v2 has already submitted a Datatrans refund call for a given item and the same call is retried within 60 minutes using the same idempotency key"),
    para("When Datatrans receives the retry request"),
    para("Then Datatrans returns the result of the original request without creating a new refund transaction, preventing the customer from being refunded twice for the same item"),
    h("Scenario 4: Clear Datatrans error - item returned to BKD status"),
    para("Given INT137v2 submits a Datatrans refund call for a given item and Datatrans returns a clear error response (e.g. SERVER_ERROR)"),
    para("When INT137v2 processes the error"),
    para("Then the item refund is KO'd on DTS and the item is returned to BKD status, and a retry within 60 minutes using the same idempotency key will return the same error from Datatrans"),
]}

payload = {"fields":{"description":description_adf,"customfield_11506":ac_adf}}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    f"{JIRA_URL}/rest/api/3/issue/DTTP25-36939",
    data=data, method="PUT",
    headers={"Authorization":f"Basic {auth}","Content-Type":"application/json","Accept":"application/json"}
)
try:
    with urllib.request.urlopen(req) as resp:
        print(f"SUCCESS: {resp.status}")
except urllib.error.HTTPError as e:
    print(f"ERROR {e.code}: {e.read().decode()}")
