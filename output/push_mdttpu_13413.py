"""Push description and acceptance criteria to MDTTPU-13413."""
import base64, ssl, json, urllib.request, urllib.error, os

JIRA_URL   = "https://smartship.atlassian.net"
JIRA_EMAIL = "sarah_suda@epam.com"
JIRA_TOKEN = os.environ.get("JIRA_TOKEN", "")
ISSUE_KEY  = "MDTTPU-13413"

auth = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_TOKEN}".encode()).decode()
HEADERS = {
    "Authorization": f"Basic {auth}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def jira_put(path, body):
    url = f"{JIRA_URL}{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=HEADERS, method="PUT")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            raw = r.read().decode()
            return r.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def jira_get(path):
    url = f"{JIRA_URL}{path}"
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            raw = r.read().decode()
            return r.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def parse_inline(text: str) -> list:
    nodes = []
    remaining = text
    while "**" in remaining:
        idx = remaining.index("**")
        pre = remaining[:idx]
        rest = remaining[idx + 2:]
        if "**" not in rest:
            break
        end_idx = rest.index("**")
        bold_text = rest[:end_idx]
        remaining = rest[end_idx + 2:]
        if pre:
            nodes.append({"type": "text", "text": pre})
        if bold_text:
            nodes.append({"type": "text", "text": bold_text,
                          "marks": [{"type": "strong"}]})
    if remaining:
        nodes.append({"type": "text", "text": remaining})
    return nodes if nodes else [{"type": "text", "text": text}]


def text_to_adf(text: str) -> dict:
    if not text:
        return {"type": "doc", "version": 1, "content": []}
    content = []
    bullet_buffer = []
    para_buffer = []

    def flush_para():
        if para_buffer:
            joined = " ".join(para_buffer)
            content.append({"type": "paragraph", "content": parse_inline(joined)})
            para_buffer.clear()

    def flush_bullets():
        if bullet_buffer:
            content.append({"type": "bulletList", "content": list(bullet_buffer)})
            bullet_buffer.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            flush_para()
            flush_bullets()
        elif stripped.startswith("## "):
            flush_para()
            flush_bullets()
            content.append({
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": stripped[3:].strip()}],
            })
        elif stripped.startswith("- "):
            flush_para()
            bullet_buffer.append({
                "type": "listItem",
                "content": [{
                    "type": "paragraph",
                    "content": parse_inline(stripped[2:].strip()),
                }],
            })
        else:
            flush_bullets()
            para_buffer.append(stripped)

    flush_para()
    flush_bullets()
    return {"type": "doc", "version": 1, "content": content}


DESCRIPTION = """\
## Change Scope
INT175 (Attentive Subscription API — MuleSoft calls Attentive to subscribe a customer to marketing communications) must be updated to handle all Attentive error response codes. The change applies at the experience API level and introduces three categories of error behaviour:

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

## Rationale
INT175 currently does not have a defined error handling strategy for the full range of Attentive error codes. Without this change, the MuleSoft integration may leak suppression status or privacy-sensitive error details to the caller, or fail to distinguish user-correctable errors from unrecoverable Attentive failures.

## Resources
- MuleSoft Requirements Page: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4825547214/IA+INT175+-+Unkown+Subscription
- High Level Architecture Document: [TO BE CONFIRMED]
- API Documentation: [TO BE CONFIRMED]"""

ACCEPTANCE_CRITERIA = """\
**Scenario 1: INVALID_DESTINATION – specific error surfaced to caller**
Given Attentive returns HTTP 400 with error code INVALID_DESTINATION (the destination information — phone number, email address, or destination type — is missing, incorrectly formatted, or incomplete)
When INT175 receives the error response from Attentive
Then INT175 returns HTTP 400 to the caller with error code INVALID_DESTINATION and the Attentive-provided error message; no generic masking is applied

**Scenario 2: COMPANY_REGION_NOT_SUPPORTED – specific error surfaced to caller**
Given Attentive returns HTTP 400 with error code COMPANY_REGION_NOT_SUPPORTED (the phone number belongs to a country or region not currently enabled for this Attentive account)
When INT175 receives the error response from Attentive
Then INT175 returns HTTP 400 to the caller with error code COMPANY_REGION_NOT_SUPPORTED and the Attentive-provided error message; no generic masking is applied

**Scenario 3: ALREADY_SUBSCRIBED – specific error surfaced to caller**
Given Attentive returns HTTP 400 with error code ALREADY_SUBSCRIBED (the user is already subscribed to the requested messaging channel and subscription type)
When INT175 receives the error response from Attentive
Then INT175 returns HTTP 400 to the caller with error code ALREADY_SUBSCRIBED and the Attentive-provided error message

**Scenario 4: PHONE_INVALID_NUMBER_FOR_REGION – specific error surfaced to caller**
Given Attentive returns HTTP 400 with error code PHONE_INVALID_NUMBER_FOR_REGION (the phone number is not recognised as valid for any configured SMS region — area code does not exist, incorrect length, or reserved/non-geographic code)
When INT175 receives the error response from Attentive
Then INT175 returns HTTP 400 to the caller with error code PHONE_INVALID_NUMBER_FOR_REGION and the Attentive-provided error message; no generic masking is applied

**Scenario 5: PHONE_DOES_NOT_MATCH_ANY_COMPANY_REGION – specific error surfaced to caller**
Given Attentive returns HTTP 400 with error code PHONE_DOES_NOT_MATCH_ANY_COMPANY_REGION (the phone number is valid but does not belong to any country or region enabled on the Attentive account)
When INT175 receives the error response from Attentive
Then INT175 returns HTTP 400 to the caller with error code PHONE_DOES_NOT_MATCH_ANY_COMPANY_REGION and the Attentive-provided error message; no generic masking is applied

**Scenario 6: USER_SUPPRESSED – masked with generic error**
Given Attentive returns HTTP 400 with error code USER_SUPPRESSED (the user is currently suppressed in Attentive)
When INT175 receives the error response from Attentive
Then INT175 returns HTTP 400 to the caller with a generic error message "unable to complete subscription"; the USER_SUPPRESSED error code is NOT included in the response to the caller

**Scenario 7: SUPPRESSED – masked with generic error**
Given Attentive returns HTTP 400 with error code SUPPRESSED (the destination should not receive messages based on suppression rules or deliverability protections)
When INT175 receives the error response from Attentive
Then INT175 returns HTTP 400 to the caller with a generic error message "unable to complete subscription"; the SUPPRESSED error code is NOT included in the response to the caller

**Scenario 8: LITIGIOUS – masked with generic error**
Given Attentive returns HTTP 400 with error code LITIGIOUS (the destination has been identified as high-risk and is not eligible to receive messages)
When INT175 receives the error response from Attentive
Then INT175 returns HTTP 400 to the caller with a generic error message "unable to complete subscription"; the LITIGIOUS error code is NOT included in the response to the caller

**Scenario 9: TERMINATED – masked with generic error**
Given Attentive returns HTTP 400 with error code TERMINATED (the user's data or subscription record has been terminated due to a deletion or privacy-related request)
When INT175 receives the error response from Attentive
Then INT175 returns HTTP 400 to the caller with a generic error message "unable to complete subscription"; the TERMINATED error code is NOT included in the response to the caller

**Scenario 10: SUSPENDED – masked with generic error**
Given Attentive returns HTTP 400 with error code SUSPENDED (the subscription is currently suspended and not eligible for reactivation)
When INT175 receives the error response from Attentive
Then INT175 returns HTTP 400 to the caller with a generic error message "unable to complete subscription"; the SUSPENDED error code is NOT included in the response to the caller

**Scenario 11: UNKNOWN – returned as HTTP 500**
Given Attentive returns an error with code UNKNOWN (the request could not be processed due to an unspecified internal Attentive error — implies Attentive is broken)
When INT175 receives the UNKNOWN error response from Attentive
Then INT175 returns HTTP 500 to the caller; this is treated as an unhandled internal error, not a 400-level client error

**Scenario 12: Unrecognised Attentive error code – returned as HTTP 500**
Given Attentive returns any error code not listed in the specific or generic categories above
When INT175 receives the unrecognised error response from Attentive
Then INT175 returns HTTP 500 to the caller; unhandled error codes must not be silently swallowed or forwarded as 400s"""

payload = {
    "update": {
        "description": [{"set": text_to_adf(DESCRIPTION)}],
        "customfield_11506": [{"set": text_to_adf(ACCEPTANCE_CRITERIA)}],
    }
}

print("=== jira_update_issue: MDTTPU-13413 ===")
status, resp = jira_put(f"/rest/api/3/issue/{ISSUE_KEY}", payload)
print(f"PUT status: {status}")
if status in (200, 204):
    print("Update SUCCESSFUL")
else:
    print(f"Update FAILED: {str(resp)[:500]}")
    raise SystemExit(1)

print("\n=== jira_get_issue: MDTTPU-13413 (verification) ===")
status2, data2 = jira_get(
    f"/rest/api/3/issue/{ISSUE_KEY}?fields=summary,description,status,issuetype,customfield_11506"
)
print(f"GET status: {status2}")
if status2 == 200:
    f = data2.get("fields", {})
    print(f"Key: {data2.get('key')}")
    print(f"Summary: {f.get('summary')}")
    print(f"Status: {f.get('status', {}).get('name')}")
    print(f"Issue type: {f.get('issuetype', {}).get('name')}")

    desc = f.get("description", {})
    desc_nodes = desc.get("content", []) if isinstance(desc, dict) else []
    print(f"\nDescription nodes: {len(desc_nodes)}")
    for node in desc_nodes[:5]:
        ntype = node.get("type")
        if ntype == "heading":
            txt = "".join(c.get("text", "") for c in node.get("content", []))
            print(f"  [H2] {txt}")
        elif ntype == "paragraph":
            txt = "".join(c.get("text", "") for c in node.get("content", []))
            print(f"  [P] {txt[:80]}")
        elif ntype == "bulletList":
            print(f"  [bulletList: {len(node.get('content', []))} items]")

    ac = f.get("customfield_11506")
    if ac and isinstance(ac, dict):
        ac_nodes = ac.get("content", [])
        print(f"\nAcceptance Criteria nodes: {len(ac_nodes)}")
        # Count scenario paragraphs with bold text starting "Scenario"
        scenario_count = 0
        for node in ac_nodes:
            if node.get("type") == "paragraph":
                for inline in node.get("content", []):
                    if inline.get("type") == "text" and any(
                        m.get("type") == "strong" for m in inline.get("marks", [])
                    ):
                        if inline.get("text", "").startswith("Scenario"):
                            scenario_count += 1
        print(f"  Scenario headings found: {scenario_count}")
        for node in ac_nodes[:2]:
            if node.get("type") == "paragraph":
                parts = []
                for c in node.get("content", []):
                    marks = [m.get("type") for m in c.get("marks", [])]
                    txt = c.get("text", "")
                    parts.append(f"**{txt}**" if "strong" in marks else txt)
                print(f"  [P] {''.join(parts)[:120]}")
    else:
        print(f"\nAC field value: {str(ac)[:200]}")

    print(f"\nURL: https://smartship.atlassian.net/browse/{ISSUE_KEY}")
    print("\n=== VERIFICATION COMPLETE ===")
else:
    print(f"GET failed: {str(data2)[:300]}")
