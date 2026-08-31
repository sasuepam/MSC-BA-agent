# Tools Reference

All slash commands, agents, MCP tools, and automated hooks available in the MSC Mule BA Agent.

---

## Slash Commands

Type these in Codemie at any time.

### Workflow

| Command | What it does | When to use |
|---|---|---|
| `/ba-workflow` | Main entry point — presents the 4-option menu | Start of every feature session |
| `/ba-amend` | Interactive flag resolution — walks through validation flags one by one | After validation, or to manually re-run amendments |

### Metrics

| Command | What it does |
|---|---|
| `/ba-metrics` | Summary table for all tracked features |
| `/ba-metrics --week` | This week's features only (Mon–Fri 6pm cutoff) |
| `/ba-metrics --detail [slug]` | Full per-phase breakdown for one feature |
| `/ba-metrics --csv` | Export all metrics to `output/metrics/exports/metrics_export_[date].csv` |
| `/ba-metrics --trend` | Improvement trends across all features (avg iterations, compliance rate, structural fix %) |
| `/ba-metrics-report` | Generate the weekly BA metrics report (also runs automatically every Friday at 5pm) |

### Setup

| Command | What it does |
|---|---|
| `/setup` | First-time environment wizard — collects credentials, writes `mcp/.env`, installs dependencies |
| `/setup verify` | Ping the MCP server and confirm all integrations are reachable |

---

## Agents

Invoked automatically by `/ba-workflow`, or directly by name.

| Agent | File | What it does |
|---|---|---|
| `functional-spec-generator` | `agents/functional-spec-generator.md` | Generates the 11-section HTML functional spec from raw input materials |
| `ba-story-generator` | `agents/ba-story-generator.md` | Generates CRs and User Stories from a spec or direct input; applies ADF exclusion and splitting rules |
| `ba-validator` | `agents/ba-validator.md` | Validates all spec and story files against 8 quality rules; produces a flag report |
| `jira-publisher` | `agents/jira-publisher.md` | Updates description and acceptance criteria on existing Jira tickets |
| `confluence-publisher` | `agents/confluence-publisher.md` | Updates BA sections on an existing Confluence page; always saves as draft |

---

## MCP Tools

These are the tools Claude calls automatically via the local MCP server. You do not invoke them directly.

The MCP server must be running (`uv run msc-mcp-server` from `mcp/`) for these to work.

### Confluence

| Tool | What it does |
|---|---|
| `mcp__msc-ba__confluence_get_page` | Reads an existing Confluence page (HTML) |
| `mcp__msc-ba__confluence_get_author_info` | Reads author/version metadata from a page |
| `mcp__msc-ba__confluence_update_page` | Updates an existing page — always saves as draft |

**Rules enforced:**
- `confluence_update_page` is the only write tool — the agent never creates or deletes pages
- All writes are saved as drafts (`status: draft`) — never published directly

### Jira

| Tool | What it does |
|---|---|
| `mcp__msc-ba__jira_get_issue` | Reads an existing Jira issue |
| `mcp__msc-ba__jira_update_issue` | Updates description and acceptance criteria on an existing issue |

**Rules enforced:**
- `jira_update_issue` is the only write tool — the agent never creates, deletes, or transitions issues
- Only description and acceptance criteria fields are written — no other fields are touched

---

## Automated Hooks

These run silently on every relevant tool call. You do not need to trigger them.

### Pre-Write Validator (blocks bad Confluence writes)

**Trigger:** fires before every `confluence_update_page` call.

**Checks:**
- Blocks the write if any `[TO BE CONFIRMED]` fields are still present in the content
- Warns if required BA sections are missing (Document History, Feature Summary, Business Requirements, Use Cases, Test Scenarios)
- Warns if no BR-001 pattern is found
- Warns if no UC-001 pattern is found

If a BLOCKER condition is found, the write is blocked and the agent reports what to fix.

**Script:** `mcp/scripts/validate_before_write.py`

---

### Post-Write BA Report

**Trigger:** fires after every `confluence_update_page` call.

**Reports:**
- Count of Business Requirements, Use Cases, and NFRs on the saved page
- Count of remaining `[TO BE CONFIRMED]` markers
- SA section integrity check — confirms Solution Overview, Involved Interfaces, Sequence Diagrams, and Monitoring & Alerting Guidelines are all still present; raises an alert if any are missing
- Page URL and draft status confirmation

**Script:** `mcp/scripts/post_generate_report.py`

---

### Metrics Auto-Update

**Trigger:** fires after `Write`, `jira_update_issue`, and `confluence_update_page` tool calls.

**Updates:**
- Spec file written → records `spec.completed_at`, `spec.output_file`, `spec.duration_minutes`, extracts `feature_requirement_id` from filename
- Story file written → appends to `stories.output_files`, updates `cr_count` / `us_count`
- Validation report written → appends a validation run with structural and content violation counts parsed from the report
- Jira update → appends ticket key to `publish.jira_tickets`
- Confluence update → records `publish.confluence_page`

**Re-entrancy guard:** exits immediately if the written path is inside `output/metrics/` — prevents the hook from triggering on metrics JSON writes.

**Script:** `mcp/scripts/metrics_auto_update.py`
