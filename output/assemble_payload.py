"""
Assembles the Confluence page body for MS: Webform for US (page 5233475594).
  - Preserves SA-owned sections verbatim from the live page
  - Replaces BA-owned sections with content from the spec file
  - Appends a new Document History row (version 3)
  - Saves the page as a DRAFT via the Confluence v2 API
"""

import asyncio
import base64
import json
import os
import re
import sys

import httpx
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_DIR    = os.path.join(SCRIPT_DIR, "..", "mcp")
load_dotenv(os.path.join(MCP_DIR, ".env"))

EMAIL    = os.getenv("MSC_CONFLUENCE_EMAIL", "")
TOKEN    = os.getenv("MSC_CONFLUENCE_TOKEN", "")
BASE_URL = os.getenv("MSC_CONFLUENCE_URL", "").rstrip("/")
PAGE_ID  = "5233475594"

AUTH           = "Basic " + base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEADERS_READ   = {"Authorization": AUTH, "Accept": "application/json"}
HEADERS_WRITE  = {**HEADERS_READ, "Content-Type": "application/json"}

# ---------------------------------------------------------------------------
# Extract SA-owned sections from current page body
# ---------------------------------------------------------------------------

def extract_sa_sections(body: str) -> dict:
    P_SOL  = re.compile(r'<h1[^>]*>\s*(?:<strong>)?Solution Overview(?:</strong>)?\s*</h1>', re.I)
    P_INV  = re.compile(r'<h2[^>]*>\s*(?:<strong>)?Involved Interfaces(?:</strong>)?\s*</h2>', re.I)
    P_SEQ  = re.compile(r'<h2[^>]*>\s*(?:<strong>)?Sequence Diagrams(?:</strong>)?\s*</h2>', re.I)
    P_NFR  = re.compile(r'<h1[^>]*>\s*(?:<strong>)?Non-Functional Requirements(?:</strong>)?\s*</h1>', re.I)
    P_MON  = re.compile(r'<h1[^>]*>\s*(?:<strong>)?Monitoring and alerting guidelines(?:</strong>)?\s*</h1>', re.I)
    P_TEST = re.compile(r'<h1[^>]*>\s*(?:<strong>)?Test Scenarios', re.I)

    def between(s_pat, e_pat):
        ms = s_pat.search(body)
        me = e_pat.search(body)
        if not ms or not me:
            return ""
        return body[ms.start():me.start()]

    return {
        "solution_overview":   between(P_SOL, P_INV),
        "involved_interfaces": between(P_INV, P_SEQ),
        "sequence_diagrams":   between(P_SEQ, P_NFR),
        "monitoring":          between(P_MON, P_TEST),
    }


def extract_existing_doc_history_table(body: str) -> str:
    """Return the first table open up to (not including) </tbody></table>."""
    m = re.search(r'(<table[^>]*>.*?</tbody>)\s*</table>', body, re.DOTALL)
    return m.group(1) if m else ""


# ---------------------------------------------------------------------------
# New Document History row  (version 3)
# ---------------------------------------------------------------------------
_ACCOUNT_ID   = "557058:11488782-2212-4d90-a7b1-1dcfc29239a1"
_AUTHOR_CELL  = (
    f'<ac:link><ri:user ri:account-id="{_ACCOUNT_ID}" /></ac:link>'
    " Co-authored by MSC BA Agent"
)
_STATUS_CELL  = (
    '<ac:structured-macro ac:name="status" ac:schema-version="1">'
    '<ac:parameter ac:name="colour">Blue</ac:parameter>'
    '<ac:parameter ac:name="title">Draft</ac:parameter>'
    "</ac:structured-macro>"
)

NEW_DOC_HISTORY_ROW = (
    "<tr>"
    "<td><p>3</p></td>"
    f"<td><p>{_AUTHOR_CELL}</p></td>"
    "<td><p><time datetime=\"2026-06-08\" /></p></td>"
    "<td><p>Updated: Reference Documentation, Feature Summary, Business Requirements, "
    "Use Cases, NFRs, Test Scenarios</p></td>"
    f"<td><p>{_STATUS_CELL}</p></td>"
    "<td><p /></td>"
    "</tr>"
)

# ---------------------------------------------------------------------------
# BA section content — Webform for US (Status Match + Contact Forms Rep Code)
# ---------------------------------------------------------------------------

REFERENCE_DOCUMENTATION = """\
<h2>Reference Documentation</h2>
<table data-table-width="760" data-layout="default">
<tbody>
<tr><th><p><strong>Document</strong></p></th><th><p><strong>Link</strong></p></th></tr>
<tr>
  <td><p>TLI-XXX \u2013 Webform US</p></td>
  <td><p><a href="https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4741922817/TLI-XXX+-+Webform+US">https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4741922817/TLI-XXX+-+Webform+US</a></p></td>
</tr>
<tr>
  <td><p>MuleSoft Scope \u2013 CR INT103 / INT101</p></td>
  <td><p><a href="https://smartship.atlassian.net/browse/MDTTPU-6137">https://smartship.atlassian.net/browse/MDTTPU-6137</a></p></td>
</tr>
</tbody>
</table>"""

FEATURE_SUMMARY = """\
<h1>Feature Summary</h1>
<p>This feature covers two separate MuleSoft integration requests for the US market, both related to
webforms in the MSCBook and B2B channels. The two requests span different web forms and different
interfaces and are treated as independent deliverables.</p>
<p><strong>Requirement 1 \u2013 Status Match Agency Email Notification (INT103):</strong> When a Travel
Agency submits a Status Match form via MSCBook or B2B, no confirmation email is currently sent to the
agency upon status match completion. The US market has requested that an optional Agency Email Address
field be captured on the Status Match form, enabling Salesforce to send a completion notification email
directly to the agency representative. The email address entered on the form may differ from the
agency&#39;s registered master email; a dedicated form-level field is therefore required. INT103 will pass
the submitted value (<code>agencyEmail__c</code>) to the Salesforce Case. Salesforce is responsible for
sending the notification email using its internal email capability; expected volumes are low and within
Salesforce platform allowances. An optional Representative Code field
(<code>agencyRepresentativeId__c</code>) is also added to the Status Match form payload and passed
through INT103 with no transformation; this field is included for future use and no immediate business
process currently depends on it.</p>
<p><strong>Requirement 2 \u2013 Contact Forms Representative Code (INT101):</strong> An optional
Representative Code field (<code>agencyRepresentativeId__c</code>) is being added to the Help Center
and Need Help form payloads (MSCBook and B2B channels) handled by INT101. INT101 will pass this field
to the Salesforce Case as a pass-through with no transformation. The field is included for future use;
no immediate business process currently depends on it.</p>
<p>Both requirements are scoped to the <strong>US market</strong> and relate to separate web forms: the
Status Match form (Requirement 1 / INT103) and the Help Center / Need Help forms
(Requirement 2 / INT101).</p>"""

BUSINESS_REQUIREMENTS = """\
<h2>Business Requirements</h2>
<p>Format: As a [actor] I want to [action] so that [benefit]</p>
<table data-table-width="760" data-layout="default">
<tbody>
<tr><th><p><strong>ID</strong></p></th><th><p><strong>Requirements</strong></p></th></tr>
<tr>
  <td><p>BR-001</p></td>
  <td><p>As a Travel Agency, I want to provide my email address when submitting a Status Match request
  via MSCBook so that I receive a confirmation notification when the status match for my client is
  completed.</p></td>
</tr>
<tr>
  <td><p>BR-002</p></td>
  <td><p>As a Travel Agency, I want to provide my Representative Code when submitting a Help Center or
  Need Help request via MSCBook so that my agency representative details are captured in Salesforce for
  future reference.</p></td>
</tr>
</tbody>
</table>"""

USE_CASES = """\
<h2>Use Cases</h2>
<p><strong>Actors:</strong></p>
<ul>
<li><strong>Travel Agency (TA)</strong> \u2014 submits the Status Match form or Help Center / Need Help form via MSCBook or B2B</li>
<li><strong>Salesforce</strong> \u2014 receives Case data from MuleSoft; sends agency notification email via internal capability</li>
<li><strong>INT103</strong> \u2014 MuleSoft interface for MSC Book Status Match and B2B Status Match; passes <code>agencyEmail__c</code> and <code>agencyRepresentativeId__c</code> to Salesforce Case</li>
<li><strong>INT101</strong> \u2014 MuleSoft interface for MSC Book Help Center &amp; Need Help Forms and B2B Contact Requests; passes <code>agencyRepresentativeId__c</code> to Salesforce Case</li>
</ul>
<table data-table-width="1058" data-layout="center">
<tbody>
<tr>
  <th><p><strong>UC#</strong></p></th>
  <th><p><strong>PreCondition</strong></p></th>
  <th><p><strong>Actor/s</strong></p></th>
  <th><p><strong>Use Case</strong></p></th>
  <th><p><strong>Functionality Expected</strong></p></th>
</tr>
<tr>
  <td><p>UC-001</p></td>
  <td><p>The Travel Agency has provided an Agency Email Address on the Status Match form.</p></td>
  <td><p>Travel Agency; INT103; Salesforce</p></td>
  <td><p>Travel Agency submits Status Match form with Agency Email Address</p></td>
  <td><p>1. Travel Agency submits the Status Match form (MSCBook or B2B) providing an Agency Email Address and optionally a Representative Code.<br />
2. INT103 receives the form payload and includes <code>agencyEmail__c</code> and <code>agencyRepresentativeId__c</code> in the Salesforce Case creation request.<br />
3. Salesforce creates the Case with both fields populated.<br />
4. Salesforce sends a notification email to the Agency Email Address upon status match completion.</p></td>
</tr>
<tr>
  <td><p>UC-002</p></td>
  <td><p>The Travel Agency has NOT provided an Agency Email Address on the Status Match form.</p></td>
  <td><p>Travel Agency; INT103; Salesforce</p></td>
  <td><p>Travel Agency submits Status Match form without Agency Email Address</p></td>
  <td><p>1. Travel Agency submits the Status Match form without providing an Agency Email Address.<br />
2. INT103 receives the payload without <code>agencyEmail__c</code> and processes the request without error.<br />
3. Salesforce creates the Case without the agency email field.<br />
4. No agency notification email is sent.</p></td>
</tr>
<tr>
  <td><p>UC-003</p></td>
  <td><p>The Travel Agency has provided a Representative Code on the Help Center or Need Help form.</p></td>
  <td><p>Travel Agency; INT101; Salesforce</p></td>
  <td><p>Travel Agency submits Help Center or Need Help form with Representative Code</p></td>
  <td><p>1. Travel Agency submits the Help Center or Need Help form (MSCBook or B2B) providing a Representative Code.<br />
2. INT101 receives the form payload and includes <code>agencyRepresentativeId__c</code> in the Salesforce Case creation request (pass-through, no transformation).<br />
3. Salesforce creates the Case with the field populated.</p></td>
</tr>
</tbody>
</table>"""

NON_FUNCTIONAL_REQUIREMENTS = """\
<h1>Non-Functional Requirements</h1>
<table data-table-width="1176" data-layout="center">
<tbody>
<tr>
  <th><p>Requirement ID</p></th>
  <th><p>Interface</p></th>
  <th><p>Requirement Description</p></th>
  <th><p>Category</p></th>
  <th><p>Priority</p></th>
</tr>
<tr>
  <td><p>NFR-004</p></td>
  <td><p>INT103, INT101</p></td>
  <td><p>All MuleSoft interface changes are scoped to the US market. No HQ-specific changes are in scope
  unless separately confirmed.</p></td>
  <td><p>Compliance</p></td>
  <td><p>High</p></td>
</tr>
</tbody>
</table>"""

TEST_SCENARIOS = """\
<h1>Test Scenarios &amp; Acceptance Criteria</h1>
<table data-table-width="1158" data-layout="center">
<tbody>
<tr>
  <th><p><strong>Use Case</strong></p></th>
  <th><p><strong>Test Cases</strong></p></th>
  <th><p><strong>Acceptance Criteria</strong></p></th>
  <th><p><strong>Test Data</strong></p></th>
</tr>
<tr>
  <td><p>UC-001</p></td>
  <td><p>HAPPY PATH \u2013 INT103 receives Status Match payload with <code>agencyEmail__c</code> and <code>agencyRepresentativeId__c</code><br /><br />
Given a Travel Agency submits the Status Match form with an Agency Email Address and a Representative Code<br />
When INT103 processes the payload<br />
Then <code>agencyEmail__c</code> and <code>agencyRepresentativeId__c</code> are present in the Salesforce Case<br />
And no transformation is applied to either field</p></td>
  <td><p>Both <code>agencyEmail__c</code> and <code>agencyRepresentativeId__c</code> are stored in the Salesforce Case with the values submitted on the form. No data loss, truncation, or transformation occurs.</p></td>
  <td><p>Status Match form payload with valid <code>agencyEmail__c</code> and <code>agencyRepresentativeId__c</code> values. Representative Code allowed values are [TO BE CONFIRMED].</p></td>
</tr>
<tr>
  <td><p>UC-002</p></td>
  <td><p>HAPPY PATH \u2013 INT103 receives Status Match payload without <code>agencyEmail__c</code><br /><br />
Given a Travel Agency submits the Status Match form without an Agency Email Address<br />
When INT103 processes the payload<br />
Then INT103 processes the request successfully without error<br />
And no agency notification email is sent by Salesforce</p></td>
  <td><p>INT103 processes the payload without error when <code>agencyEmail__c</code> is absent. No downstream errors occur. No agency email is triggered.</p></td>
  <td><p>Status Match form payload with <code>agencyEmail__c</code> omitted.</p></td>
</tr>
<tr>
  <td><p>UC-003</p></td>
  <td><p>HAPPY PATH \u2013 INT101 receives Help Center / Need Help payload with <code>agencyRepresentativeId__c</code><br /><br />
Given a Travel Agency submits a Help Center or Need Help form with a Representative Code<br />
When INT101 processes the payload<br />
Then <code>agencyRepresentativeId__c</code> is present in the Salesforce Case<br />
And no transformation is applied to the field</p></td>
  <td><p><code>agencyRepresentativeId__c</code> is stored in the Salesforce Case with the value submitted on the form. No data loss, truncation, or transformation occurs.</p></td>
  <td><p>Help Center / Need Help form payload with a valid <code>agencyRepresentativeId__c</code> value. Representative Code allowed values are [TO BE CONFIRMED].</p></td>
</tr>
</tbody>
</table>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    # -- Fetch current page --------------------------------------------------
    print("Fetching current Confluence page...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{BASE_URL}/wiki/api/v2/pages/{PAGE_ID}",
            headers=HEADERS_READ,
            params={"body-format": "storage"},
        )
    if not resp.is_success:
        print(f"ERROR: {resp.status_code} {resp.text[:300]}")
        sys.exit(1)

    data            = resp.json()
    current_version = data["version"]["number"]
    page_title      = data["title"]
    current_body    = data["body"]["storage"]["value"]
    print(f"  Title:   {page_title}")
    print(f"  Version: {current_version}")

    # -- Extract SA sections -------------------------------------------------
    sa = extract_sa_sections(current_body)
    for key, val in sa.items():
        status = f"{len(val)} chars" if val else "NOT FOUND (placeholder will be used)"
        print(f"  SA '{key}': {status}")

    # -- Build Document History ----------------------------------------------
    doc_hist_open = extract_existing_doc_history_table(current_body)
    if doc_hist_open:
        document_history = doc_hist_open + NEW_DOC_HISTORY_ROW + "\n</tbody></table>"
    else:
        print("  WARNING: doc history table not found; building fresh table")
        document_history = (
            "<table data-table-width=\"760\" data-layout=\"default\"><tbody>"
            "<tr><th><p>VERSION</p></th><th><p>AUTHOR(S)</p></th><th><p>DATE</p></th>"
            "<th><p>REMARKS</p></th><th><p>STATUS</p></th><th><p>TICKETS</p></th></tr>"
            + NEW_DOC_HISTORY_ROW
            + "</tbody></table>"
        )

    # -- Assemble full body in template order --------------------------------
    fallback_sa = {
        "solution_overview":   "<h1>Solution Overview</h1><p>[Populated by Solution Architect.]</p>",
        "involved_interfaces": "<h2>Involved Interfaces</h2><p>[Populated by Solution Architect.]</p>",
        "sequence_diagrams":   "<h2>Sequence Diagrams</h2><p>[Populated by Solution Architect.]</p>",
        "monitoring":          "<h1>Monitoring and Alerting Guidelines</h1><p>[Populated by Solution Architect.]</p>",
    }

    new_body = "\n\n".join([
        document_history,
        REFERENCE_DOCUMENTATION,
        FEATURE_SUMMARY,
        BUSINESS_REQUIREMENTS,
        USE_CASES,
        sa.get("solution_overview")   or fallback_sa["solution_overview"],
        sa.get("involved_interfaces") or fallback_sa["involved_interfaces"],
        sa.get("sequence_diagrams")   or fallback_sa["sequence_diagrams"],
        NON_FUNCTIONAL_REQUIREMENTS,
        sa.get("monitoring")          or fallback_sa["monitoring"],
        TEST_SCENARIOS,
    ])

    print(f"\n  Assembled body: {len(new_body)} chars")

    # -- Save payload locally ------------------------------------------------
    payload = {
        "id":      PAGE_ID,
        "status":  "draft",
        "title":   page_title,
        "version": {"number": 1},
        "body":    {"storage": {"value": new_body, "representation": "storage"}},
    }
    out_path = os.path.join(SCRIPT_DIR, "confluence_payload.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"  Payload written to {out_path}")

    # -- Push as DRAFT -------------------------------------------------------
    print(f"\nPushing DRAFT to Confluence page {PAGE_ID}...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        put_resp = await client.put(
            f"{BASE_URL}/wiki/api/v2/pages/{PAGE_ID}",
            headers=HEADERS_WRITE,
            json=payload,
        )

    print(f"  HTTP status: {put_resp.status_code}")
    if put_resp.is_success:
        result = put_resp.json()
        webui  = result.get("_links", {}).get("webui", "")
        print(f"  Page ID:   {result.get('id')}")
        print(f"  Title:     {result.get('title')}")
        print(f"  Status:    {result.get('status')}")
        print(f"  Version:   {result.get('version', {}).get('number')}")
        print(f"  URL:       {BASE_URL}/wiki{webui}")
        print("\nSUCCESS \u2014 page saved as DRAFT.")
    else:
        print(f"  ERROR body: {put_resp.text[:600]}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
