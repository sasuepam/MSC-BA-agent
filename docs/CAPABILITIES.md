# What the BA Agent Can Do

A complete picture of capabilities, with examples of what to type.

---

## 1. Preprocess Raw Input Materials (Intake)

**Start here when inputs are PDFs or meeting recordings.**

```
/intake

PDF: docs/requirements_free_balcony_upgrade.pdf
VTT: recordings/kickoff_meeting.vtt
Video: recordings/kickoff_meeting.mp4
```

```
/intake

Confluence page: https://msccruises.atlassian.net/wiki/spaces/DTTP/pages/[id]/[title]
```

What happens:
1. PDFs are extracted using text parsing + AI vision via `distill-doc`
2. Meeting recordings: VTT transcript enriched with video frame descriptions via `enrich-meeting`
3. Confluence pages: fetched live, navigation stripped, substantive content preserved
4. All outputs saved as structured Markdown to `output/intake/`
5. `intake_summary.md` written with key topics and extraction counts

The intake output files are passed automatically to the spec generator when you run `/ba-workflow` and choose to preprocess first.

**Time saving:** 30–60 min of manual note-taking → 2–5 min of automated extraction.

---

## 2. Generate Functional Specifications

**The foundation of every feature.** From raw input to a complete 11-section HTML spec.

```
/ba-workflow
1

[paste requirements email here]
```

```
/ba-workflow
1

Requirements: https://msccruises.atlassian.net/wiki/spaces/DTTP/pages/[id]/[title]
Additional context: [paste stakeholder email]
```

What happens:
1. Reads the spec template before generating any content
2. Reads all source materials (URLs fetched live, files read, text used directly)
3. Fills all 7 BA-owned sections following the template exactly
4. Leaves 4 SA-owned sections as placeholders — never overwrites Solution Architect content
5. Marks any missing information as `[TO BE CONFIRMED]`
6. Runs `spec_validator.py` before saving — auto-fixes structural issues and retries once
7. Reports file path, TBC count, and template compliance result

Output: `output/specs/functional_spec_[feature_name].html`

**BA-owned sections filled automatically:** Document History, Reference Documentation, Feature Summary, Business Requirements (BR-### user story format), Use Cases (UC-### with MuleSoft API named), Non-Functional Requirements (NFR-###), Test Scenarios & Acceptance Criteria.

**SA-owned sections — never touched:** Solution Overview, Involved Interfaces, Sequence Diagrams, Monitoring and Alerting Guidelines.

---

## 3. Generate Jira-Ready Stories

**From spec or direct input.** Produces individual `.md` files — one per CR, one per US.

```
/ba-workflow
2
```

```
"Generate stories from output/specs/functional_spec_free_balcony_upgrade.html"
```

**Direct input (no spec needed):**
```
/ba-workflow
2

Direct input mode. Interfaces:
- INT710v2 — Booking Enrichment (new interface)
- INT025 — Passenger Profile (existing, adding coupon code field)
- ADF108 — (exclude)

Requirements:
1. System must support loyalty tier upgrades for balcony cabins
2. Upgrade eligibility must be evaluated at booking confirmation
```

What happens:
1. Reads both CR and US templates before generating
2. Applies ADF exclusion rule — ADF-prefixed interfaces produce no stories
3. Applies splitting rules: new interface → US; existing interface change → CR
4. Generates each story following the template exactly
5. Runs `story_validator.py` per story before saving — auto-retries once on failure
6. Saves each story as a separate `.md` file with sequential numbering
7. Reports CR count, US count, ADF exclusions, and template compliance per story

Output: `output/stories/[feature]_cr_001.md`, `[feature]_us_001.md`, etc.

---

## 4. Validate Artefacts — 14 Rules

**Quality gate before handover.** Optional — choose automated, conversational, or both.

```
"Run validation on the current spec and stories files."
```

```
"Run validation — structural rules only. I'll deal with content quality separately."
```

What happens:
1. Reads all files in `output/specs/` and `output/stories/`
2. Runs structural rules 9–14 first (template compliance — hard BLOCKERs)
3. Runs content quality rules 1–8 after (traceability and completeness)
4. Saves `output/validation/validation-report.md`
5. Reports BLOCKER / WARNING / INFO counts by category

**Structural rules (9–14):**

| Rule | What it checks |
|---|---|
| 9 | All 11 spec sections present; table columns correct; no inline CSS |
| 10 | SA-owned sections present and unmodified |
| 11 | All 7 BA sections have substantive content |
| 12 | CR: required sections, summary ≤10 words, BDD ≥2 scenarios |
| 13 | US: required sections, summary ≤12 words, INT### format, BDD ≥3 scenarios |
| 14 | No empty critical fields; no vague BDD language |

**Content quality rules (1–8):**

| Rule | What it checks |
|---|---|
| 1 | Any `[TO BE CONFIRMED]` still present |
| 2 | BDD criteria missing Given/When/Then or measurable outcome |
| 3 | Blank documentation / reference fields |
| 4 | ADF-prefixed interface found in any story |
| 5 | Wrong CR/US split (new interface given CR, or change given US) |
| 6 | Users field blank or Change Scope missing owning system |
| 7 | Use case IDs in spec with no matching test scenario |
| 8 | Business requirements with no traceable story |

---

## 5. Amend Artefacts Interactively

**Walk through every flag. Apply, edit, or skip — file-by-file.**

```
/ba-amend
```

```
"Fix FLAG-003 from the validation report. Apply the suggested fix."
```

```
"For FLAG-007, the correct value is: INT710v2 Booking Enrichment API. Apply that edit."
```

```
"Accept all INFO-level fixes without confirming each one."
```

What happens:
1. Reads the validation report
2. Walks through flags in order: structural BLOCKERs first, then content BLOCKERs, then WARNINGs, then INFOs
3. For each flag: shows the issue and suggested fix; you choose Accept / Edit / Skip
4. Applies fixes directly to the relevant spec or story file
5. Reports Amendment Summary: structural fixes, content fixes, applied / edited / skipped counts

---

## 6. Publish to Jira

**Update existing tickets with formatted descriptions and acceptance criteria.**

```
"Publish the stories to Jira ticket DTTP25-1234."
```

```
"Publish to DTTP25-1234, DTTP25-1235, and DTTP25-1236."
```

```
"Show me a preview of the Jira description for DTTP25-1234 before updating."
```

What happens:
1. Fetches current ticket via Jira REST API
2. Reads the matching story `.md` file from `output/stories/`
3. Shows preview of description and acceptance criteria
4. Asks for explicit confirmation before writing
5. Re-fetches ticket to verify the update
6. Reports the ticket URL

**Important:** The agent never creates or deletes tickets, and never transitions status.

---

## 7. Publish to Confluence

**Update BA sections of an existing spec page, always saving as draft.**

```
"Publish the spec to: https://msccruises.atlassian.net/wiki/spaces/DTTP/pages/[id]/[title]"
```

What happens:
1. Fetches the current page including body HTML
2. Extracts and preserves SA-owned sections verbatim
3. Replaces BA-owned sections with content from the spec file
4. Adds a new Document History row (version-bumped, current date, sections updated)
5. Shows a full preview and asks for explicit confirmation
6. Always saves as **Draft** — a human must publish manually
7. Reports the page URL and Document History entry created

---

## 8. Answer BA Context Questions

**Instant answers about MSC conventions, rules, and patterns.**

```
"What's the ADF exclusion rule and which interface prefixes does it apply to?"
```

```
"What's the difference between a CR and a User Story in this context?"
```

```
"Walk me through why each interface was given a CR versus a US in the last stories run."
```

```
"Can I skip validation and go straight to publishing?"
```

```
"What's the correct format for Business Requirements in the spec?"
```

---

## 9. Track and Report Metrics

**Per-feature timing, token usage, and quality trends.**

```
/ba-metrics
```

```
/ba-metrics --week
```

```
/ba-metrics --detail free_balcony_upgrade
```

```
/ba-metrics --trend
```

```
/ba-metrics-report
```

What `/ba-metrics` tracks per feature:
- Intake phase used (yes/no)
- Validation mode chosen
- Template auto-fix counts (how many pre-save retries were triggered)
- Per-phase timing and iteration counts
- Structural vs content violation counts per validation run
- Structural vs content fix counts per amend run
- Feedback loop count (amend + re-validate cycles)
- Token usage and estimated USD cost

Weekly summary report auto-generated every **Friday at 5pm GMT+1** to `output/metrics/weekly_reports/`.

---

## What the Agent Does NOT Do

- **Invent content** — missing information is always marked `[TO BE CONFIRMED]`, never guessed
- **Create Jira tickets** — only updates existing ones (description and ACs only)
- **Create or delete Confluence pages** — only updates BA sections of an existing page
- **Overwrite SA-owned spec sections** — Solution Overview, Involved Interfaces, Sequence Diagrams, and Monitoring are protected
- **Generate stories for ADF interfaces** — ADF-prefixed interfaces are always excluded
- **Publish to production Confluence without confirmation** — always requires explicit approval; always saves as draft
