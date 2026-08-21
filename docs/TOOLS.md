# Tools Reference

All slash commands, agents, validators, and MCP tools available in the BA Agent.

---

## Slash Commands

Type these in Codemie at any time. The `/ba-workflow` orchestrator also invokes the relevant agents automatically.

### Main workflows

| Command | What it does | When to use |
|---|---|---|
| `/ba-workflow` | Main orchestration menu — spec, stories, validate, amend, publish | Start of every feature session |
| `/intake` | Preprocess raw input materials — PDFs, meeting recordings, Confluence pages, text | Before spec generation when inputs are in binary or unstructured format |
| `/ba-amend` | Interactive flag resolution — Accept / Edit / Skip per flag | After validation; also invoked automatically by `/ba-workflow` when BLOCKERs are found |

### Metrics and reporting

| Command | What it does |
|---|---|
| `/ba-metrics` | Summary table of all tracked features (slug, status, time, loops, tokens, cost) |
| `/ba-metrics --week` | This week's features only (Monday to today) |
| `/ba-metrics --detail [slug]` | Full per-phase breakdown for one feature |
| `/ba-metrics --csv` | Export all metrics to `output/metrics/metrics_export.csv` |
| `/ba-metrics --trend` | Feedback loops and structural fix ratio trends across all features |
| `/ba-metrics-report` | Generate full weekly summary report on demand (also auto-runs Fridays at 5pm GMT+1) |

### Setup

| Command | What it does |
|---|---|
| `/setup` | First-time configuration wizard — credentials, MCP server, dependency install |
| `/setup verify` | Ping MCP server and check all integrations are reachable |

---

## Agents

Each agent is a Markdown system prompt in `agents/`. When invoked, the agent reads its prompt and executes the defined workflow. Agents are stateless — they read from and write to the `output/` directory.

| Agent file | Role | Invoked by |
|---|---|---|
| `intake-preprocessor.md` | Extracts PDFs (distill-doc), enriches meeting recordings (enrich-meeting), fetches Confluence pages; writes clean Markdown to `output/intake/` | `/intake` skill, or via `/ba-workflow` intake phase |
| `functional-spec-generator.md` | Reads spec template; generates 11-section HTML spec from input materials; runs `spec_validator.py` before saving | `/ba-workflow` option 1, 3 |
| `ba-story-generator.md` | Reads CR and US templates; generates stories from spec or direct input; runs `story_validator.py` per story before saving; outputs one `.md` per story | `/ba-workflow` option 2, 3 |
| `ba-validator.md` | Applies 14 rules (structural 9–14 first, then content 1–8); saves `output/validation/validation-report.md` | `/ba-workflow` option 3, 4; or invoked directly |
| `jira-publisher.md` | Fetches Jira ticket; previews description and ACs; updates on confirmation | `/ba-workflow` publish phase |
| `confluence-publisher.md` | Fetches Confluence page; replaces BA sections; preserves SA sections; saves as draft | `/ba-workflow` publish phase |

---

## Python Validators

Two validators enforce template compliance before any artefact is saved. They are called automatically by the generating agents, and can also be run manually on any output file.

### spec_validator.py

**Location:** `knowledge/templates/spec_validator.py`  
**Invoked by:** `functional-spec-generator` (pre-save) and `ba-validator` (Rule 9)  
**Manual usage:**

```bash
python3 knowledge/templates/spec_validator.py output/specs/functional_spec_[name].html
```

**What it checks:**
- All 11 required `<h2>` section headings present
- Use Cases table has 6 required column headers (UC#, PreCondition, Actor/s, Use Case, Functionality Expected, Open Questions)
- Business Requirements use "As a [actor] I want [action] so that [benefit]" format
- NFR table has 5 required column headers (Requirement ID, Interface, Requirement Description, Category, Priority)
- Test Scenarios table has required column headers (Use Case, Test Cases, Acceptance Criteria, Test Data)
- No `<style>` blocks or inline `style=` attributes

**Output:** `OK` (exit code 0) or JSON array of violations (exit code 1).

---

### story_validator.py

**Location:** `knowledge/templates/story_validator.py`  
**Invoked by:** `ba-story-generator` (pre-save, per story) and `ba-validator` (Rules 12–13)  
**Manual usage:**

```bash
python3 knowledge/templates/story_validator.py --type=cr output/stories/[feature]_cr_001.md
python3 knowledge/templates/story_validator.py --type=us output/stories/[feature]_us_001.md
```

**CR checks:**
- All required CR sections present (Summary, Change Scope, Interfaces Affected, Rationale, Resources, Acceptance Criteria)
- Summary is ≤10 words
- Acceptance Criteria use Given/When/Then format with at least 2 scenarios (happy path + 1 error/alt)
- Change Scope names a specific endpoint, field, or behaviour (not vague)

**US checks:**
- All required US sections present (Summary, User Story Statement, Story Details, Use Cases, Functionality, Acceptance Criteria, Documentation, Open Questions)
- Summary is ≤12 words
- Interface Name follows "INT### Name" format
- Functionality section has all 4 subsections (Authentication, Happy Path, Alternative Paths, Error Scenarios)
- Acceptance Criteria use Given/When/Then format with at least 3 scenarios

**Output:** `OK` (exit code 0) or JSON array of violations (exit code 1).

---

## MCP Server Tools

The MCP server (`mcp/`) exposes Confluence and Jira operations as callable tools. These are invoked automatically by the agents — you do not call them directly.

The server runs locally at `http://localhost:8080/mcp`. Start it before each session:

```bash
cd mcp
uv run msc-mcp-server
```

### Confluence tools

| Tool | What it does | Used by |
|---|---|---|
| `confluence_get_page` | Fetch page body HTML, version number, and status | `confluence-publisher`, `ba-validator` (Rule 10) |
| `confluence_search` | Full-text page search by query | Agent context lookups |
| `confluence_update_page` | Update page content (requires version number) | `confluence-publisher` |
| `confluence_create_page` | Create a new page (used only if explicitly directed) | `confluence-publisher` (rare) |
| `confluence_extract_ia` | Parse Interface Agreement HTML tables to structured JSON | Context enrichment |

### Jira tools

| Tool | What it does | Used by |
|---|---|---|
| `jira_get_issue` | Fetch issue fields (summary, status, description, assignee) | `jira-publisher` |
| `jira_search` | Search by JQL query | Agent context lookups |
| `jira_create_issue` | Create a new issue | `jira-publisher` (rarely; always confirms first) |
| `jira_update_issue` | Update issue fields (description, ACs) | `jira-publisher` |

---

## Intake Skills

The intake phase uses two installed skills for binary input processing.

| Skill | What it does | Triggered by |
|---|---|---|
| `distill-doc` | Extracts text from PDF files using classical text parsing + AI vision; merges outputs into structured Markdown | `/intake` when a PDF path is provided |
| `enrich-meeting` | Extracts video frames at scene changes; enriches a VTT transcript with frame descriptions to capture screen content discussed in the meeting | `/intake` when a VTT + video path is provided |

Both skills write their output to `output/intake/[source]_intake.md`.

---

## Output File Structure

```
output/
├── intake/
│   ├── [source]_intake.md          ← preprocessed input (one per source)
│   └── intake_summary.md           ← extraction summary and key topics
│
├── specs/
│   └── functional_spec_[name].html ← 11-section HTML spec
│
├── stories/
│   ├── [feature]_cr_001.md         ← Change Request (one file per story)
│   ├── [feature]_cr_002.md
│   └── [feature]_us_001.md         ← User Story (one file per story)
│
├── validation/
│   └── validation-report.md        ← 14-rule flag report; structural first
│
└── metrics/
    ├── metrics_[slug].json          ← per-feature timing, tokens, fix counts
    └── weekly_reports/
        └── ba_metrics_[date].md    ← weekly summary (auto-generated Fridays)
```
