# BA Validation Report

**Generated:** 12/Aug/2026
**Files validated:**
- `output/specs/functional_spec_crm_booking_b2b_b2c_calculated_fields.html`
- `output/stories/crm-booking-b2b-b2c-calculated-fields.html`

---

## Summary

| Severity | Count |
|---|---|
| BLOCKER  | 1 |
| WARNING  | 3 |
| INFO     | 2 |
| **TOTAL**| **6** |

> No blockers from ADF slippage or CR/US misclassification; one blocker for unresolved TBC fields that must be resolved before publication. Three warnings address untestable acceptance criteria and missing system ownership detail; two info flags cover missing documentation links.

---

## Flags

### FLAG-001

- **Rule:**        Rule 1 — TO BE CONFIRMED fields still present
- **Severity:**    BLOCKER
- **File:**        functional_spec_crm_booking_b2b_b2c_calculated_fields.html AND crm-booking-b2b-b2c-calculated-fields.html
- **Section:**     Document History / Reference Documentation / Resources & Dependencies
- **Issue:**       Multiple `[TO BE CONFIRMED]` placeholders remain unresolved across both files: (1) Spec — Document History Author field; (2) Spec — all 8 Reference Documentation links (CRM2-11045, DTTP25-41761, Confluence A007, A0086, A87, INT-024.1, INT-025, INT-100 interface agreement links); (3) Stories — CRM2-11045 and DTTP25-41761 links; (4) Stories — DTS JSON field names and paths for the B2B/B2C boolean in all three interface payloads.
- **Suggested fix:** Obtain the Confluence and Jira URLs for CRM2-11045 and DTTP25-41761. Confirm Confluence page links for A007, A0086, A87. Obtain DTS JSON field names and paths for the B2B/B2C boolean in INT-100, INT-025, and INT-024.1 from the DTS team. Populate the Document History Author field with the BA name.

---

### FLAG-002

- **Rule:**        Rule 2 — Vague or untestable acceptance criteria
- **Severity:**    WARNING
- **File:**        crm-booking-b2b-b2c-calculated-fields.html
- **Section:**     Acceptance Criteria (final Given/When/Then block)
- **Issue:**       The final acceptance criterion bundles three separate concerns — latency (performance), backward compatibility (schema), and security controls — into a single Given/When/Then statement. No SLA thresholds or latency targets are quoted and no verification mechanism is specified.
- **Suggested fix:** Split into three separate acceptance criteria: one for performance (reference NFR-001 with a specific latency ceiling), one for backward compatibility (reference NFR-005, specify verification method), and one for security (reference NFR-006, state how it will be confirmed). Each should stand alone as a testable Given/When/Then.

---

### FLAG-003

- **Rule:**        Rule 2 — Vague or untestable acceptance criteria
- **Severity:**    WARNING
- **File:**        functional_spec_crm_booking_b2b_b2c_calculated_fields.html AND crm-booking-b2b-b2c-calculated-fields.html
- **Section:**     Test Scenarios & Acceptance Criteria — UC-002 (INT-025) and UC-003 (INT-024.1)
- **Issue:**       UC-002 has only TC-007 (boolean field absent) with no test case for a malformed or non-boolean value. UC-003 has only TC-010 (boolean field absent) with no malformed-value case. UC-001 (INT-100) includes TC-004 for malformed values. NFR-003 explicitly requires graceful handling of malformed values across all three interfaces, so INT-025 and INT-024.1 are under-tested.
- **Suggested fix:** Add TC-011 for UC-002 (INT-025 — malformed boolean value) and TC-012 for UC-003 (INT-024.1 — malformed boolean value) following the pattern of TC-004. Update the CR acceptance criteria to call out the malformed-value error path for INT-025 and INT-024.1.

---

### FLAG-004

- **Rule:**        Rule 6 — Stories missing system owner
- **Severity:**    WARNING
- **File:**        crm-booking-b2b-b2c-calculated-fields.html
- **Section:**     Change Scope
- **Issue:**       Change Scope bullet points do not identify the owning team responsible for each item. The documentation update bullet does not state whether it is a MuleSoft BA/SA action or a Marketing team action.
- **Suggested fix:** Add a brief owner annotation to each Change Scope bullet, e.g. "(Owner: MuleSoft integration team)" for passthrough mapping items and "(Owner: Marketing team)" for the documentation update.

---

### FLAG-005

- **Rule:**        Rule 3 — Missing documentation links
- **Severity:**    INFO
- **File:**        functional_spec_crm_booking_b2b_b2c_calculated_fields.html
- **Section:**     Reference Documentation
- **Issue:**       All eight documentation links in the Reference Documentation table are unresolved (`[TO BE CONFIRMED]`): CRM2-11045, DTTP25-41761, Confluence A007, A0086, A87, INT-024.1, INT-025, and INT-100 interface agreement links.
- **Suggested fix:** Populate each link with the actual Confluence page URL or Jira ticket URL before the spec is shared with stakeholders.

---

### FLAG-006

- **Rule:**        Rule 3 — Missing documentation links
- **Severity:**    INFO
- **File:**        crm-booking-b2b-b2c-calculated-fields.html
- **Section:**     Resources & Dependencies
- **Issue:**       CRM2-11045 and DTTP25-41761 are listed as dependencies but both links are `[TO BE CONFIRMED]`.
- **Suggested fix:** Insert the Jira ticket URLs for CRM2-11045 and DTTP25-41761 into the link fields.

---

## Passed checks

- **Rule 4 — ADF interfaces that slipped through:** No ADF-prefixed interfaces found in either file.
- **Rule 5 — Inconsistent CR / User Story splits:** All three interfaces correctly treated as existing interfaces and grouped into a single CR. No new interfaces assigned a CR; no existing interface changes given a User Story.
- **Rule 7 — Use Cases not referenced in Test Scenarios:** All three use cases fully covered. UC-001 by TC-001–TC-004; UC-002 by TC-005–TC-007; UC-003 by TC-008–TC-010. All appear in the CR acceptance criteria.
- **Rule 8 — Business Requirements without a corresponding story:** Both BRs traceable to the CR. BR-001 addressed by passthrough mapping scope items; BR-002 by the Interfaces Affected section and Change Scope documentation update bullet.
