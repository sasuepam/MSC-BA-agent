import json, urllib.request, urllib.error, base64, os

JIRA_URL = "https://smartship.atlassian.net"
EMAIL = "sarah_suda@epam.com"
TOKEN = os.environ.get("JIRA_TOKEN", "")
ISSUE = "MDTTPU-10926"

def p(text): return {"type": "paragraph", "content": [{"type": "text", "text": text}]}
def strong(text): return {"type": "text", "text": text, "marks": [{"type": "strong"}]}
def plain(text): return {"type": "text", "text": text}
def br(): return {"type": "hardBreak"}
def link(url): return {"type": "inlineCard", "attrs": {"url": url}}

def bullet(*items):
    return {"type": "bulletList", "content": [{"type": "listItem", "content": [{"type": "paragraph", "content": [plain(i)]}]} for i in items]}

def bullet_nested(label, subitems):
    return {
        "type": "listItem",
        "content": [
            {"type": "paragraph", "content": [plain(label)]},
            {"type": "bulletList", "content": [
                {"type": "listItem", "content": [{"type": "paragraph", "content": [plain(s)]}]} for s in subitems
            ]}
        ]
    }

def bullet_link(label, url):
    return {
        "type": "listItem",
        "content": [{"type": "paragraph", "content": [plain(label + ": "), link(url)]}]
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
        # Splitting Rationale
        {"type": "heading", "attrs": {"level": 2}, "content": [plain("Splitting Rationale")]},
        p("The ticket covers a single business rule — a TOKENIZATION flag — applied consistently to two outbound interfaces (A013 and A070) across two integrations (INT007 and INT146). The logic is identical in both cases and was confirmed together by Ivan Cattaneo in the comments. One CR is appropriate; splitting would create redundancy with no benefit."),
        {
            "type": "table",
            "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
            "content": [
                {"type": "tableRow", "content": [
                    {"type": "tableHeader", "attrs": {}, "content": [{"type": "paragraph", "content": [strong("#")]}]},
                    {"type": "tableHeader", "attrs": {}, "content": [{"type": "paragraph", "content": [strong("Summary")]}]},
                    {"type": "tableHeader", "attrs": {}, "content": [{"type": "paragraph", "content": [strong("Rationale")]}]},
                ]},
                {"type": "tableRow", "content": [
                    {"type": "tableCell", "attrs": {}, "content": [p("CR-1")]},
                    {"type": "tableCell", "attrs": {}, "content": [p("Tokenization flag on A013 and A070 (INT007 & INT146)")]},
                    {"type": "tableCell", "attrs": {}, "content": [p("Unified change: same field, same conditional logic, same downstream systems")]},
                ]},
            ]
        },
        {"type": "rule"},
        # CR fields
        {"type": "paragraph", "content": [strong("Type: "), plain("CR")]},
        {"type": "paragraph", "content": [strong("Summary: "), plain("Tokenization Flag on A013 and A070 for INT007 and INT146")]},
        {"type": "paragraph", "content": [strong("Jira Ticket: "), plain("MDTTPU-8082")]},
        {"type": "paragraph", "content": [strong("Description:")]},
        {"type": "paragraph", "content": [strong("Change Scope:")]},
        {
            "type": "bulletList",
            "content": [
                {"type": "listItem", "content": [p("Add a new TOKENIZATION flag to outbound interfaces A013 and A070, applicable to both INT007 (Booking Request) and INT146 (MyMSC Finalize Payment) flows")]},
                {"type": "listItem", "content": [p("The flag value is derived from the B2CW savePaymentMethod field and the outcome of the R007 token-save process")]},
                bullet_nested(
                    "A013 mapping — field: recipients[].context{}.Tokenization (string type):",
                    [
                        'savePaymentMethod = false \u2192 value: "null"',
                        'savePaymentMethod = true AND R007 saves token \u2192 value: "true"',
                        'savePaymentMethod = true AND R007 does NOT save token \u2192 value: "false"',
                    ]
                ),
                bullet_nested(
                    "A070 mapping — field: _msccruisessa.webform.support.tokenization (boolean type):",
                    [
                        "savePaymentMethod = false \u2192 field is omitted entirely",
                        "savePaymentMethod = true AND R007 saves token \u2192 value: true",
                        "savePaymentMethod = true AND R007 does NOT save token \u2192 value: false",
                    ]
                ),
                {"type": "listItem", "content": [p("Data mapping sections in IA INT007V3 and IA INT146 updated accordingly (confirmed by Ivan Cattaneo)")]},
            ]
        },
        {"type": "paragraph", "content": [strong("Rationale:")]},
        p("To support payment tokenization in the MSC ecosystem, downstream marketing and CDP systems (A013 and A070) require explicit notification of whether a payment method token was successfully saved during a booking or payment finalisation flow. This change introduces a conditional Tokenization field that reflects the combined outcome of the customer's save preference (B2CW savePaymentMethod) and the actual R007 token-save result, enabling A013 and A070 to correctly profile customers and personalise future communications."),
        {"type": "paragraph", "content": [strong("Resources:")]},
        {
            "type": "bulletList",
            "content": [
                {"type": "listItem", "content": [p("Mule Specification Document: [TO BE CONFIRMED]")]},
                {"type": "listItem", "content": [p("High Level Architecture Document: [TO BE CONFIRMED]")]},
                {
                    "type": "listItem",
                    "content": [
                        p("API Documentation:"),
                        {"type": "bulletList", "content": [
                            {"type": "listItem", "content": [{"type": "paragraph", "content": [plain("IA INT007V3 - Booking Request: "), link("https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4537876481/IA+INT007V3+-+Booking+Request")]}]},
                            {"type": "listItem", "content": [{"type": "paragraph", "content": [plain("IA INT146 - MyMSC Finalize Payment: "), link("https://msccruises.atlassian.net/wiki/spaces/DTP/pages/3941924882/IA+INT146+-+MyMSC+Finalize+Payment")]}]},
                        ]}
                    ]
                },
                {"type": "listItem", "content": [{"type": "paragraph", "content": [plain("Confluence Page - A013 NEW - External System API Transactional Campaigns: "), link("https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4663967745/A013+NEW+-+External+System+API+Transactional+Campaigns")]}]},
                {"type": "listItem", "content": [{"type": "paragraph", "content": [plain("Confluence Page - A070 NEW - Webforms and triggers to CDP: "), link("https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4252074747/A070+NEW+-+Webforms+and+triggers+to+CDP")]}]},
            ]
        },
        {"type": "paragraph", "content": [strong("Acceptance Criteria (BDD):")]},
        bdd(
            "Given a PAYMENT SUCCESS event is received with savePaymentMethod = false",
            'When INT007 or INT146 processes the event and triggers A013 and A070',
            'Then A013 sends recipients[].context{}.Tokenization = "null" (string)',
            'And A070 does not include the _msccruisessa.webform.support.tokenization field',
        ),
        bdd(
            "Given a PAYMENT SUCCESS event is received with savePaymentMethod = true",
            "And the R007 process successfully saves the payment token",
            "When INT007 or INT146 processes the event and triggers A013 and A070",
            'Then A013 sends recipients[].context{}.Tokenization = "true" (string)',
            "And A070 sends _msccruisessa.webform.support.tokenization = true (boolean)",
        ),
        bdd(
            "Given a PAYMENT SUCCESS event is received with savePaymentMethod = true",
            "And the R007 process does NOT save the payment token",
            "When INT007 or INT146 processes the event and triggers A013 and A070",
            'Then A013 sends recipients[].context{}.Tokenization = "false" (string)',
            "And A070 sends _msccruisessa.webform.support.tokenization = false (boolean)",
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
