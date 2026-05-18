# BA Validation Report

**Generated:** 15/May/2026
**Files validated:**
- `output/specs/functional_spec_bpc_customer_contact.html`
- Stories file: none (no stories file exists — Rules 4, 5, 6, 8 applied with available evidence only)

---

## Summary

| Severity | Count |
|---|---|
| BLOCKER  | 1 |
| WARNING  | 3 |
| INFO     | 8 |
| **TOTAL**| 12 |

> 1 blocker (unresolved TBC fields across the spec) must be resolved before this spec is ready for development; 3 warnings relating to vague acceptance criteria should also be addressed to prevent ambiguity during testing.

---

## Flags

### FLAG-001

- **Rule:**        Rule 1 — TO BE CONFIRMED fields still present
- **Severity:**    BLOCKER
- **File:**        `output/specs/functional_spec_bpc_customer_contact.html`
- **Section:**     Document History
- **Issue:**       The TICKETS field in the Document History table still contains `[TO BE CONFIRMED]`. This must reference the Jira ticket(s) that track this change before the spec is handed over to development.
- **Suggested fix:** Replace `[TO BE CONFIRMED]` in the TICKETS column with the relevant Jira ticket key(s) (e.g. DTTP-XXXX). If the ticket has not been created yet, create it and add the key before publishing.

---

### FLAG-002

- **Rule:**        Rule 1 — TO BE CONFIRMED fields still present
- **Severity:**    BLOCKER
- **File:**        `output/specs/functional_spec_bpc_customer_contact.html`
- **Section:**     Reference Documentation
- **Issue:**       All six Reference Documentation links are `[TO BE CONFIRMED]`: BPC Customer Contact Source Requirements, INT006 IA, INT007 IA, INT004.4 IA, INT139 IA, and INT145 IA. These are placeholder entries that provide no navigable reference for developers or reviewers.
- **Suggested fix:** Replace each `[TO BE CONFIRMED]` link with the actual Confluence page URL or SharePoint/document URL for the relevant Interface Agreement and source requirements document. If any IA does not yet exist, note it explicitly (e.g. "Not yet published — pending SA") rather than leaving a TBC placeholder.

---

### FLAG-003

- **Rule:**        Rule 1 — TO BE CONFIRMED fields still present
- **Severity:**    BLOCKER
- **File:**        `output/specs/functional_spec_bpc_customer_contact.html`
- **Section:**     Test Scenarios & Acceptance Criteria — TC-001 through TC-013 (Test Data column)
- **Issue:**       Every test scenario (TC-001 to TC-013) has `[TO BE CONFIRMED]` in the Test Data field. TC-012 and TC-013 additionally have `mobilePhone: [TO BE CONFIRMED]` in the test data values. Without concrete test data, testers cannot execute the scenarios and QA sign-off is blocked.
- **Suggested fix:** For each test case, populate the Test Data column with: the target MuleSoft environment URL, the Postman collection or test harness reference, and any specific data setup steps (e.g. booking option ID in DTS for UC-003/TC-006). For TC-012 and TC-013, also supply the `mobilePhone` sample value (use the same test number used in TC-011, e.g. `"227977157"`, unless INT139/INT145 require a different market number).

---

### FLAG-004

- **Rule:**        Rule 2 — Vague or untestable acceptance criteria
- **Severity:**    WARNING
- **File:**        `output/specs/functional_spec_bpc_customer_contact.html`
- **Section:**     Test Scenarios & Acceptance Criteria — TC-001
- **Issue:**       The Then clause of TC-001 reads "Then the API must reject the request." This is incomplete — it names the action but omits the expected measurable outcome (HTTP status code and response body content) within the BDD statement itself. The detail is present in the Acceptance Criteria column but the Given/When/Then structure is not self-contained and would fail a strict BDD review.
- **Suggested fix:** Rewrite the Then clause to include the full expected outcome, for example: "Then the API must return HTTP 400 Bad Request with a response body containing a message indicating that the phone number is required for the first passenger, and the booking must not be submitted to DTS."

---

### FLAG-005

- **Rule:**        Rule 2 — Vague or untestable acceptance criteria
- **Severity:**    WARNING
- **File:**        `output/specs/functional_spec_bpc_customer_contact.html`
- **Section:**     Test Scenarios & Acceptance Criteria — TC-005
- **Issue:**       The Then clause of TC-005 reads "Then the API must handle this gracefully." This is explicitly vague — "gracefully" has no measurable outcome. The Acceptance Criteria column acknowledges that the expected behaviour is unconfirmed ("Behaviour must be confirmed with the development team"), which means this scenario is not yet testable.
- **Suggested fix:** Before finalising the spec, confirm with the development team whether the expected behaviour for a mismatched prefix is: (a) return HTTP 400 with a descriptive error, or (b) pass the number through without stripping and proceed. Once confirmed, rewrite the Then clause with the specific outcome, e.g. "Then the API must return HTTP 400 Bad Request with an error message stating the phone number prefix does not match the provided mobilePhonePrefix value." Remove the ambiguous "must be confirmed" note from the Acceptance Criteria column once resolved.

---

### FLAG-006

- **Rule:**        Rule 2 — Vague or untestable acceptance criteria
- **Severity:**    WARNING
- **File:**        `output/specs/functional_spec_bpc_customer_contact.html`
- **Section:**     Test Scenarios & Acceptance Criteria — UC-003 / TC-006
- **Issue:**       TC-006 covers only the happy path for the HoldOption flow. There is no error or edge case scenario for UC-003 — specifically, no test case covers what happens when `PAXCellular` is empty or absent in DTS when the HoldOption flow is triggered. Rule 2 requires at least one error or edge case scenario alongside the happy path.
- **Suggested fix:** Add a second test case under UC-003 that covers the scenario where `PAXCellular` is empty or null in the DTS booking option at the point the HoldOption flow is triggered. Define the expected API behaviour (error response, fallback, or warning log) and the corresponding HTTP status or observable outcome.

---

### FLAG-007

- **Rule:**        Rule 3 — Missing documentation links
- **Severity:**    INFO
- **File:**        `output/specs/functional_spec_bpc_customer_contact.html`
- **Section:**     Reference Documentation
- **Issue:**       All six documentation link fields are blank (`[TO BE CONFIRMED]`). While this is also flagged as a BLOCKER under Rule 1, it is separately noted here as an INFO to confirm that the Reference Documentation section was actively checked for completeness, not just for TBC syntax.
- **Suggested fix:** See FLAG-002 for the actionable fix. Ensure all six links are populated with navigable URLs pointing to the source IA documents and the BPC Customer Contact requirements page in Confluence before publishing.

---

### FLAG-008

- **Rule:**        Rule 5 — Inconsistent CR / User Story splits
- **Severity:**    INFO
- **File:**        `output/specs/functional_spec_bpc_customer_contact.html` (stories file: none)
- **Section:**     N/A — stories file not yet generated
- **Issue:**       No stories file exists for this spec yet. Rule 5 cross-references the spec against generated stories to check for incorrect CR/US splits. This check cannot be completed until stories are generated by the ba-story-generator agent.
- **Suggested fix:** Run the ba-story-generator against this spec to produce `output/stories/bpc_customer_contact.md`, then re-run the ba-validator. Per the splitting rules: all interfaces listed (INT006, INT007, INT007.1, INT007.2, INT004.4, INT139, INT145) are existing interfaces, so this feature should be covered by one or more CRs — not User Stories. Verify that the story generator applies the correct CR type for all changes.

---

### FLAG-009

- **Rule:**        Rule 6 — Stories missing system owner
- **Severity:**    INFO
- **File:**        Stories file not yet generated
- **Section:**     N/A
- **Issue:**       No stories file exists. The system owner / consuming system check (Rule 6) cannot be applied until stories are generated. This is noted as a reminder to validate once the stories file is produced.
- **Suggested fix:** After generating stories, re-run the ba-validator and confirm that each CR's Change Scope field names the owning system or team responsible for each interface (e.g. "MuleSoft EINT team — INT006, INT007 BookRequest").

---

### FLAG-010

- **Rule:**        Rule 8 — Business Requirements without a corresponding story
- **Severity:**    INFO
- **File:**        `output/specs/functional_spec_bpc_customer_contact.html` (stories file: none)
- **Section:**     Business Requirements — BR-001
- **Issue:**       BR-001 (correct phone field mapping to DTS BookRequest and HoldOption for PAX 1) has no traceable story. This is the core mapping fix and should be covered by a CR targeting INT006 and INT007 variants.
- **Suggested fix:** Ensure the generated CR for INT006/INT007 explicitly references BR-001 in its Rationale or description. Re-validate after stories are generated.

---

### FLAG-011

- **Rule:**        Rule 8 — Business Requirements without a corresponding story
- **Severity:**    INFO
- **File:**        `output/specs/functional_spec_bpc_customer_contact.html` (stories file: none)
- **Section:**     Business Requirements — BR-002
- **Issue:**       BR-002 (mandatory phone number validation for first passenger) has no traceable story. This introduces a new validation behaviour and must be covered by a CR.
- **Suggested fix:** Ensure the CR for INT006/INT007 covers the mandatory validation rule for PAX 1, or create a separate CR if the team determines this is a distinct enough change to warrant one. Re-validate after stories are generated.

---

### FLAG-012

- **Rule:**        Rule 8 — Business Requirements without a corresponding story
- **Severity:**    INFO
- **File:**        `output/specs/functional_spec_bpc_customer_contact.html` (stories file: none)
- **Section:**     Business Requirements — BR-003, BR-004, BR-005
- **Issue:**       BR-003 (downstream system alignment — CH001, S008, GEN001, A070), BR-004 (Datatrans Init Transaction customer.phone fix for INT004.4, INT139, INT145), and BR-005 (no unintended side effects) have no traceable stories. BR-003 and BR-004 likely warrant their own CRs given the distinct systems and interfaces involved.
- **Suggested fix:** When generating stories, confirm that separate CRs are raised for: (1) the downstream propagation fix (BR-003, covering CH001/S008/GEN001/A070), and (2) the Datatrans Init Transaction fix (BR-004, covering INT004.4/INT139/INT145). BR-005 is a non-regression constraint and should be referenced in the acceptance criteria of each CR rather than as a standalone story. Re-validate after stories are generated.

---

## Passed checks

- **Rule 4 — ADF interface slippage:** No ADF-prefixed interface IDs (e.g. ADF108, ADF204) were found anywhere in the spec. All interface IDs use the correct INT/DT/CH/S/GEN/A naming conventions.
- **Rule 7 — Use Cases not referenced in Test Scenarios:** All five Use Cases defined in the spec (UC-001 through UC-005) are referenced in at least one Test Scenario row. Full coverage confirmed: UC-001 → TC-001, TC-002; UC-002 → TC-003, TC-004, TC-005; UC-003 → TC-006; UC-004 → TC-007 to TC-010; UC-005 → TC-011 to TC-013.
