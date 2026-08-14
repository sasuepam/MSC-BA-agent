import json, urllib.request, urllib.error, base64, os

JIRA_URL = "https://smartship.atlassian.net"
EMAIL = "sarah_suda@epam.com"
TOKEN = os.environ.get("JIRA_TOKEN", "")
ISSUE = "DTTP25-38409"

def p(text):
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}

def strong(text):
    return {"type": "text", "text": text, "marks": [{"type": "strong"}]}

def plain(text):
    return {"type": "text", "text": text}

def br():
    return {"type": "hardBreak"}

def link(url):
    return {"type": "inlineCard", "attrs": {"url": url}}

def bullet_nested(label, subitems):
    return {
        "type": "listItem",
        "content": [
            {"type": "paragraph", "content": [plain(label)]},
            {"type": "bulletList", "content": [
                {"type": "listItem", "content": [{"type": "paragraph", "content": [plain(s)]}]}
                for s in subitems
            ]}
        ]
    }

def bdd(*lines):
    content = []
    for i, line in enumerate(lines):
        keyword, rest = line.split(" ", 1)
        if i > 0:
            content.append(br())
        content.append(strong(keyword + " "))
        content.append(plain(rest))
    return {"type": "paragraph", "content": content}

description = {
    "type": "doc",
    "version": 1,
    "content": [
        # Header fields
        {"type": "paragraph", "content": [strong("Type: "), plain("CR")]},
        {"type": "paragraph", "content": [strong("Summary: "), plain("Chain 1 \u2013 Extend US CDP Routing to CAN and USA Market Codes for DTS Post-Booking Interfaces (INT100, INT025, INT024.1)")]},
        {"type": "paragraph", "content": [strong("Jira Ticket: "), plain("DTTP25-38409")]},
        {"type": "paragraph", "content": [strong("Description:")]},
        {"type": "paragraph", "content": [strong("Change Scope:")]},
        {
            "type": "bulletList",
            "content": [
                {"type": "listItem", "content": [p("Update INT100V2, INT025V2, and INT024.1V2 on chain 1 to apply the CDP routing logic already implemented on chain 2")]},
                {"type": "listItem", "content": [p("Current chain 2 condition: marketCode = \u201cUS\u201d \u2192 CDP US; else \u2192 CDP HQ")]},
                {"type": "listItem", "content": [p("Chain 1 new condition: marketCode = \u201cCAN\u201d OR \u201cUSA\u201d \u2192 CDP US; else \u2192 CDP HQ")]},
                {"type": "listItem", "content": [p("INT100V2: update routing condition governing A086 (Booking Profile Streaming API) calls to CDP")]},
                {"type": "listItem", "content": [p("INT025V2: update routing condition governing A087 (Booking Event Streaming API) calls to CDP")]},
                {"type": "listItem", "content": [p("INT024.1V2: update routing condition governing A007 (Booking Event Streaming API) calls to CDP")]},
                {"type": "listItem", "content": [p("All other processing logic is unchanged: event filtering, participant minimum minor age business rule, BPID generation, CruiseID/PassengerID splitting, Customer Hub lookups (INT024.1), and retry behaviour")]},
            ]
        },
        {"type": "paragraph", "content": [strong("Rationale:")]},
        p("Chain 1 currently routes all DTS post-booking events to CDP HQ regardless of market. Following the same pattern delivered on chain 2, chain 1 must now direct US and Canadian market data to the US CDP instance. The dual market code trigger (CAN + USA) reflects the broader geographic scope of the US CDP in the chain 1 environment, ensuring both markets are correctly profiled in the US CDP while all other markets continue to route to HQ."),
        {"type": "paragraph", "content": [strong("Resources:")]},
        {
            "type": "bulletList",
            "content": [
                {"type": "listItem", "content": [p("Mule Specification Document: [TO BE CONFIRMED]")]},
                {"type": "listItem", "content": [p("High Level Architecture Document: [TO BE CONFIRMED]")]},
                {"type": "listItem", "content": [p("API Documentation: [TO BE CONFIRMED]")]},
                {"type": "listItem", "content": [{"type": "paragraph", "content": [
                    plain("Confluence Page \u2013 MS US Market Config and CDP US Sandbox Environment Support: "),
                    link("https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4688281612/MS+US+Market+Config+and+CDP+US+Sandbox+Environment+Support")
                ]}]},
                {"type": "listItem", "content": [p("Reference chain 2 implementation: MDTTPU-1247")]},
            ]
        },
        {"type": "paragraph", "content": [strong("Acceptance Criteria (BDD):")]},
        bdd(
            "Given INT100V2 processes a BookingEvent on chain 1 with marketCode \"CAN\" or \"USA\"",
            "When the event is routed to CDP",
            "Then A086 (Booking Profile) is sent to CDP US",
            "And CDP HQ does not receive the request",
        ),
        bdd(
            "Given INT100V2 processes a BookingEvent on chain 1 with a market code other than \"CAN\" or \"USA\"",
            "When the event is routed to CDP",
            "Then A086 (Booking Profile) is sent to CDP HQ",
            "And CDP US does not receive the request",
        ),
        bdd(
            "Given INT025V2 processes a BookingEvent on chain 1 with marketCode \"CAN\" or \"USA\"",
            "When the event is routed to CDP",
            "Then A087 (Booking Event) is sent to CDP US",
            "And CDP HQ does not receive the request",
        ),
        bdd(
            "Given INT025V2 processes a BookingEvent on chain 1 with a market code other than \"CAN\" or \"USA\"",
            "When the event is routed to CDP",
            "Then A087 (Booking Event) is sent to CDP HQ",
            "And CDP US does not receive the request",
        ),
        bdd(
            "Given INT024.1V2 processes a BookingEvent on chain 1 with marketCode \"CAN\" or \"USA\"",
            "When the event is routed to CDP",
            "Then A007 (Booking Event) is sent to CDP US",
            "And CDP HQ does not receive the request",
        ),
        bdd(
            "Given INT024.1V2 processes a BookingEvent on chain 1 with a market code other than \"CAN\" or \"USA\"",
            "When the event is routed to CDP",
            "Then A007 (Booking Event) is sent to CDP HQ",
            "And CDP US does not receive the request",
        ),
        bdd(
            "Given any of INT100V2, INT025V2, or INT024.1V2 processes a BookingEvent",
            "When CDP routing is evaluated",
            "Then all existing processing logic (event filtering, minor age rules, BPID generation, splitting, Customer Hub lookups) behaves identically to the current chain 1 implementation",
        ),
    ]
}

payload = json.dumps({"fields": {"description": description}}).encode("utf-8")
creds = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
req = urllib.request.Request(
    f"{JIRA_URL}/rest/api/3/issue/{ISSUE}",
    data=payload,
    method="PUT",
    headers={
        "Authorization": f"Basic {creds}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
)
try:
    with urllib.request.urlopen(req) as resp:
        print(f"SUCCESS {resp.status}")
except urllib.error.HTTPError as e:
    print(f"ERROR {e.code}: {e.read().decode()}")
