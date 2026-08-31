# BA Agent — Capabilities Reference

What the MSC Mule BA Agent can and cannot do.

---

## What It Does

### Generate functional specifications

From any combination of raw input — emails, meeting notes, Confluence pages, Jira tickets, pasted text, sequence diagrams — the agent generates a structured 11-section HTML functional specification scoped to the MuleSoft team's deliverables.

The spec covers:
- **Solution context** (Feature Summary, Business Requirements, Use Cases) — business language, solution-level, not API-specific
- **API layer** (NFRs, Test Scenarios & Acceptance Criteria) — scoped to the MuleSoft API(s) being built or changed

Gaps in source material are always marked `[TO BE CONFIRMED]` — never invented.

---

### Generate Jira-ready BA stories

From a functional spec (or direct interface input), the agent generates Change Requests and User Stories, one `.md` file per story, named with the requirement ID prefix.

**Story type rules:**
- New interface → **User Story** (one per interface, never grouped)
- Change to an existing interface → **Change Request**
- ADF-prefixed interfaces → **excluded** (owned by another team)
- Same logical change across multiple existing interfaces → **one CR**
- Different logical changes → **separate CRs**

Each story follows a strict template (CR or US) and is ready to paste into Jira.

---

### Validate quality

Reads all spec and story files and produces a structured validation report with flags at three severity levels: BLOCKER, WARNING, INFO.

Eight rules are checked:

| Rule | Severity |
|---|---|
| TBC fields still present | BLOCKER |
| ADF interface slipped into stories | BLOCKER |
| Inconsistent CR / User Story split | BLOCKER |
| Vague or untestable acceptance criteria | WARNING |
| Missing system owner | WARNING |
| Use cases not covered by test scenarios | WARNING |
| Missing documentation links | INFO |
| Business requirements without a traceable story | INFO |

---

### Amend artefacts interactively

Walks through every flag in the validation report one at a time (BLOCKERs first). For each flag the user chooses: accept the suggested fix, provide their own text, or skip. Changes are applied directly to the relevant file.

Tracks structural fixes (wrong story construction) and content fixes (missing or incomplete content) separately for metrics.

---

### Publish to Jira

Updates the description and acceptance criteria fields on existing Jira tickets. Never creates, deletes, or transitions tickets.

---

### Publish to Confluence

Updates BA-owned sections on an existing Confluence requirements page. Always saves as a draft — never publishes directly. SA-owned sections (Solution Overview, Involved Interfaces, Sequence Diagrams, Monitoring and Alerting Guidelines) are never modified.

---

### Track pipeline metrics

Every feature run is automatically tracked in `output/metrics/metrics_[slug].json`. Metrics include time per phase, iteration counts, CR/US counts, validation results (structural vs content split), amendment history, feedback loops, and publish targets.

View metrics with `/ba-metrics`, export to CSV with `/ba-metrics --csv`, and see weekly trends with `/ba-metrics --trend`. A weekly summary report runs automatically every Friday at 5pm.

---

## What It Does NOT Do

| Limitation | Detail |
|---|---|
| **Invent content** | Gaps are always marked `[TO BE CONFIRMED]` |
| **Create Jira tickets** | Updates existing tickets only — never creates or deletes |
| **Create Confluence pages** | Updates existing pages only — never creates or deletes |
| **Publish Confluence drafts** | Always saves as draft; a human must publish manually |
| **Modify SA-owned sections** | Solution Overview, Involved Interfaces, Sequence Diagrams, and Monitoring & Alerting Guidelines are never touched |
| **Generate stories for ADF interfaces** | ADF-prefixed interfaces are excluded by design |
| **Run full validation from Stories only** | Option 2 stops after story generation — run option 4 to validate |
| **Handle card payments or booking data** | The agent generates documentation, not integration code |

---

## Scope: What the Agent Knows

The agent is pre-loaded with MSC programme context via `knowledge/MSC_CONTEXT.md`:

- DTTP programme background and rollout timeline
- All key systems (DTS, CHUB, Salesforce, AEM, CDP, AJO, Genesys, Datatrans, Algolia, MuleSoft)
- Booking process flow
- Interface naming conventions (INT, ADF prefix rules)
- CR/US split rules
- 11-section functional spec format
- CR and US template fields
- BA vs SA section ownership
- Validation rule definitions

You do not need to explain any of this context when using the agent — it already knows it.
