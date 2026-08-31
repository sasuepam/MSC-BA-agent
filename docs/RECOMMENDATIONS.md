# Recommendations & Best Practices

Guidance for getting the best results from the MSC Mule BA Agent.

---

## Before You Start

### Gather all input materials before opening the workflow

The agent can only work from what you provide. Before running `/ba-workflow`, collect:

- The requirements source (email thread, Teams message, meeting notes, Confluence page URL, Jira ticket)
- The requirement ID (`NEW-XXXX`) — available from the backlog
- Any sequence diagrams or architecture notes relevant to the feature
- Interface IDs involved (e.g. INT118, INT025) and whether each is new or an existing change

The more complete your input, the fewer `[TO BE CONFIRMED]` gaps in the output — and the fewer validation BLOCKERs you'll need to resolve.

### Know whether you need a spec first

- **New feature, no existing spec:** use option 3 (full end-to-end) or option 1 (spec only, then continue later)
- **Spec already exists:** use option 2 (stories only) → from spec
- **Providing interface names directly without a spec:** use option 2 → direct input
- **Returning to a feature you started before:** use option 4 (validate and publish)

---

## Spec Phase

### Resolve TBCs before generating stories

Stories inherit gaps from the spec. A `[TO BE CONFIRMED]` in a spec field becomes a BLOCKER in validation after stories are generated. It's faster to fill in TBCs in the spec first, before running story generation.

After the spec is saved, the agent lists all `[TO BE CONFIRMED]` fields. Work through them before continuing.

### Be explicit about ADF interfaces

If the source materials mention ADF-prefixed interfaces (e.g. ADF108), they should appear in the spec's Use Cases for context — but explicitly note they are ADF and out of scope for the MuleSoft team. This prevents them from being misclassified during story generation.

### Give the agent the full email thread, not a summary

The agent extracts business rules, constraints, and edge cases from raw text. A paraphrase loses detail. Paste the full email or meeting notes — the agent will filter what's relevant.

---

## Stories Phase

### Check the ADF exclusion list

After stories are generated, confirm the ADF exclusion list matches your expectations. If a non-ADF interface was accidentally excluded, or an ADF interface appeared in a story, run `/ba-amend` to fix it before publishing.

### Verify the CR/US split

Review the story type assigned to each interface:
- Every **new** interface should be a User Story
- Every **existing interface change** should be a Change Request
- The same logical change across multiple existing interfaces should be **one CR**, not separate CRs

If the split is wrong, the validator will catch it as a BLOCKER (Rule 5). Fix it in the amend phase.

### One story file per CR or User Story

Each story is saved as a separate `.md` file named `<req-id>-[slug]-cr-001.md` or `<req-id>-[slug]-us-001.md`. If you're updating an existing Jira ticket, the story filename makes it easy to identify which file maps to which ticket.

---

## Validation Phase

### Always validate before publishing

Even if the spec and stories look correct, the validator catches issues that are easy to miss manually — vague acceptance criteria, missing system owners, use cases without test coverage, and business requirements with no traceable story. Run it every time.

### Treat BLOCKERs as mandatory

BLOCKERs (TBC fields, ADF slippage, wrong CR/US splits) must be resolved before publishing. The workflow enforces this, but if you bypass it you risk pushing incomplete or miscategorised stories to Jira.

### Re-validate after amendments

The amend phase can resolve one flag while inadvertently introducing an edge case elsewhere (e.g. editing an acceptance criterion incorrectly). A quick re-validation after `/ba-amend` confirms you are clean before publishing.

---

## Amend Phase

### Accept where you can, edit where you must

"Accept fix" applies the agent's suggested resolution automatically — use it for mechanical fixes (removing TBC placeholders with confirmed values, removing ADF stories). "Edit manually" is for cases where you know the right content and want to control it exactly.

### Don't skip BLOCKERs unless you have a plan

Skipping a BLOCKER is allowed but the workflow warns you. If you skip because you need to confirm a value with a stakeholder, note the FLAG number so you can come back to it with `/ba-amend` after the spec is updated.

---

## Publishing

### Confluence: always review the draft before publishing

The agent updates BA sections and appends a Document History row. Before the SA publishes the draft, check:
- The Document History version number and sections updated are correct
- All `[TO BE CONFIRMED]` markers are gone
- The SA-owned sections (Solution Overview, Involved Interfaces, Sequence Diagrams, Monitoring & Alerting Guidelines) are unchanged

### Jira: confirm the ticket mapping before updating

When publishing multiple stories, double-check which story file maps to which Jira ticket — especially if CRs cover multiple interfaces. The agent will ask you to confirm before writing.

### Don't close the MCP server terminal mid-session

If the MCP server stops, Jira and Confluence publish calls will fail. Keep the MCP server terminal open for the full duration of your session. If it stops unexpectedly, restart it with `uv run msc-mcp-server` from the `mcp/` directory.

---

## Metrics

### Use `/ba-metrics` to spot patterns

After a few features, run `/ba-metrics --trend` to see where time is being spent and whether template compliance is improving. Common patterns:
- High feedback loop count → input materials are incomplete; gather more context upfront
- High structural fix rate (>10%) → CR/US split decisions are being corrected frequently; review the splitting rules
- Long spec phase duration → complex features with many TBCs; resolve gaps before generating stories

### Weekly report

A weekly summary report runs automatically every Friday at 5pm and is saved to `output/metrics/weekly_reports/`. Run `/ba-metrics-report` manually at any time to generate it on demand.
