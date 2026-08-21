# MSC Mule BA Agent — User Guide

An AI-assisted toolkit for Business Analysts on the MSC Cruises MuleSoft Integration team (DTTP programme). It takes raw input materials — emails, meeting notes, Confluence pages, PDFs, meeting recordings, or pasted text — and walks you through the full BA pipeline: preprocessing inputs, generating a functional specification, producing Jira-ready BA stories, validating quality, amending issues, and publishing to Jira and Confluence.

The agent never invents content. Any information it cannot find in your input materials is marked `[TO BE CONFIRMED]` for you to fill in.

---

## Contents

- [First-time setup](#first-time-setup)
- [Every session — start here](#every-session--start-here)
- [Running the BA workflow](#running-the-ba-workflow)
- [What to provide as input materials](#what-to-provide-as-input-materials)
- [Pipeline overview](#pipeline-overview)
- [Workflow phases in detail](#workflow-phases-in-detail)
  - [Phase 0 — Intake preprocessing (optional)](#phase-0--intake-preprocessing-optional)
  - [Phase 1 — Functional spec generation](#phase-1--functional-spec-generation)
  - [Phase 2 — BA story generation](#phase-2--ba-story-generation)
  - [Phase 3 — Validation (optional)](#phase-3--validation-optional)
  - [Phase 4 — Amendment](#phase-4--amendment)
  - [Phase 5 — Publish to Jira](#phase-5--publish-to-jira)
  - [Phase 6 — Publish to Confluence](#phase-6--publish-to-confluence)
- [Template validation](#template-validation)
- [Story templates](#story-templates)
- [Functional spec — sections and ownership](#functional-spec--sections-and-ownership)
- [Functional spec — writing standards](#functional-spec--writing-standards)
- [What gets produced](#what-gets-produced)
- [Agents and skills](#agents-and-skills)
- [Metrics tracking](#metrics-tracking)
- [Output folder structure](#output-folder-structure)
- [Reference documents](#reference-documents)
- [Key things to know](#key-things-to-know)
- [Troubleshooting](#troubleshooting)

---

## First-time setup

Follow [`docs/SETUP.md`](docs/SETUP.md) once before using the agent for the first time. It covers installing Claude Code, configuring your Atlassian API credentials, and starting the MCP server.

---

## Every session — start here

You need **two terminals** open each time you work.

**Terminal 1 — MCP server** (keep this running in the background):
```bash
cd "C:\Users\[your_user]\MSC_BA_Agent\MSC_BA_Agent\mcp"
uv run msc-mcp-server
```

> **Windows note:** If `uv` is not found, use the full path in Command Prompt or PowerShell:
> ```
> %APPDATA%\Python\Python314\Scripts\uv.exe run msc-mcp-server
> ```

You should see:
```
Starting MSC MCP Server on 0.0.0.0:8080 (transport=streamable-http)
Application startup complete.
```

If port 8080 is already in use, the server from a previous session is still running — you do not need to restart it.

**Terminal 2 — Claude Code** (this is where you work):
```bash
cd "C:\Users\[your_user]\MSC_BA_Agent\MSC_BA_Agent"
codemie-claude
```

---

## Running the BA workflow

Once Claude Code is open, type:

```
/ba-workflow
```

You will see a menu:

```
1. Spec only            — generate a functional spec from input materials
2. Stories only         — generate Jira BA stories from a spec or direct input
3. Full end-to-end      — spec → stories → validate → amend → publish
4. Validate and publish — validate existing output and publish to Jira / Confluence
```

For options 1 and 3, you will also be asked whether to run **intake preprocessing** first — useful when your input materials are PDFs or meeting recordings that need extracting before the spec can be generated.

Choose the option that matches what you need. Claude will guide you through each step interactively.

You can also invoke any individual agent or skill directly — see [Agents and skills](#agents-and-skills) below.

---

## What to provide as input materials

When prompted for input materials, you can provide any combination of:

- **Pasted text** — copy and paste an email, Teams message, meeting notes, or requirements description directly into the chat
- **File paths** — e.g. `C:\Users\[your_user]\Documents\requirements.docx`
- **PDF files** — run `/intake` first to extract content (see [Phase 0](#phase-0--intake-preprocessing-optional))
- **Meeting recordings** — provide a VTT transcript file + video file; `/intake` will enrich the transcript with screen context
- **Confluence page URLs** — e.g. `https://msccruises.atlassian.net/wiki/spaces/...` — the agent fetches the page live via the MCP server
- **Jira ticket URLs** — e.g. `https://smartship.atlassian.net/browse/MDTTPU-1234`
- **Sequence diagrams** — paste PlantUML directly into the chat
- **Images** — describe what an image shows or share a file path

The more detail you provide, the fewer `[TO BE CONFIRMED]` gaps will appear in the output.

---

## Pipeline overview

```
Input materials
      │
      ▼  (optional)
┌─────────────────────────────┐
│  /intake                     │  → output/intake/*.md
│  intake-preprocessor (agent) │    Extracts PDFs, enriches meeting recordings,
│                              │    fetches Confluence pages, structures text
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  functional-spec-generator   │  → output/specs/functional_spec_[name].html
│  (agent)                     │    Reads template, validates structure pre-save
│                              │    11 sections: BA-owned (7) + SA-owned (4)
└──────────────┬──────────────┘
               │  (choose: conversational review / automated validation / both)
               ▼
┌─────────────────────────────┐
│  ba-story-generator          │  → output/stories/[initiative]_cr_001.md etc.
│  (agent)                     │    Input: spec file OR direct requirements
│                              │    Validates each story pre-save; auto-retries
└──────────────┬──────────────┘
               │  (optional)
               ▼
┌─────────────────────────────┐
│  ba-validator                │  → output/validation/validation-report.md
│  (agent)                     │    Rules 9–14: structural (BLOCKERs first)
│                              │    Rules 1–8:  content quality (after structure)
└──────────────┬──────────────┘
               │  (if blockers found)
               ▼
┌─────────────────────────────┐
│  /ba-amend                   │    Interactive: Accept fix / Edit manually / Skip
│  (skill)                     │    Applies fixes to specs and stories files
└──────────────┬──────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌─────────────┐  ┌──────────────────────┐
│  jira-      │  │  confluence-          │
│  publisher  │  │  publisher            │
│  (agent)    │  │  (agent)              │
│             │  │                       │
│ Updates     │  │ Updates BA sections   │
│ description │  │ only. Preserves SA    │
│ and ACs on  │  │ sections. Always      │
│ existing    │  │ saves as DRAFT        │
│ tickets     │  └──────────────────────┘
└─────────────┘
```

> **Architecture diagram:** See [`docs/architecture-diagram.html`](docs/architecture-diagram.html) for a full visual map of how all agents, skills, validators, and output folders connect.

---

## Workflow phases in detail

### Phase 0 — Intake preprocessing (optional)

**Command:** `/intake` (standalone) or prompted by `ba-workflow`
**Agent:** `intake-preprocessor`

Cleans and structures raw input materials before BA processing. Run this when your inputs are PDFs, meeting recordings, or other unstructured formats.

**What it supports:**

| Input type | How it is processed |
|---|---|
| PDF files | Extracted via classical text parsing + AI vision (distill-doc skill); merged output |
| Meeting recordings | VTT transcript enriched with screen frame descriptions (enrich-meeting skill) |
| Confluence pages | Fetched live and stripped to substantive content |
| Pasted text | Written directly to a structured markdown file |

**Output:** Structured `.md` files in `output/intake/` and a summary at `output/intake/intake_summary.md`.

You can run `/intake` at any time — it does not require the workflow to be running. Pass the output files as input materials to the spec generator.

---

### Phase 1 — Functional spec generation

**Agent:** `functional-spec-generator`

Reads all provided input materials and generates a structured HTML functional specification scoped to the MuleSoft team's deliverables.

The spec covers:
- The **overall solution** in the Feature Summary, Business Requirements, and Use Cases sections — giving developers and reviewers full business context
- The **API layer specifically** in the NFRs and Test Scenarios — written for the API(s) the MuleSoft team will build or change

**What the agent does:**
1. Reads the spec template (`knowledge/templates/functional_specification_template.html`) before generating any content
2. Reads all input materials (pasted text, files, Confluence pages, URLs, or `output/intake/` files from the intake phase)
3. Identifies the overall solution and the specific MuleSoft API(s) involved
4. Fills in all 7 BA-owned sections; preserves all 4 SA-owned sections unchanged
5. Marks gaps as `[TO BE CONFIRMED]` rather than inventing content
6. Runs `spec_validator.py` before saving — auto-fixes structural issues; retries once on failure
7. Saves the spec to `output/specs/functional_spec_[feature_name].html`
8. Reports the file path, all TO BE CONFIRMED fields, and template validation result

For Test Scenarios, every Use Case must have at least one happy path test, one alternative path test, and one error scenario. Missing categories are flagged as gaps — never silently omitted.

After spec generation, you choose how to review before proceeding to stories:
- **Conversational** — ask the agent to fix any issues in chat
- **Automated** — run `ba-validator` with structural Rules 9–11
- **Both** — conversational first, then automated as a final check

---

### Phase 2 — BA story generation

**Agent:** `ba-story-generator`

Generates Jira-ready BA stories (Change Requests and User Stories). Supports two input modes:

| Input mode | When to use |
|---|---|
| **From spec** | Read the functional spec from `output/specs/` and derive all stories from it |
| **Direct input** | Provide a list of interfaces and requirements directly — no spec needed |

**What the agent does:**
1. Reads both story templates (`change_request_template.html`, `user_story_template.html`) before generating
2. Applies the ADF exclusion rule and splitting logic (see below)
3. Generates each story following the template exactly
4. Runs `story_validator.py` on each story before saving — auto-retries once on failure
5. Saves each story as a separate Markdown file to `output/stories/`
6. Reports template compliance per story

**Output filenames:** `output/stories/[initiative]_cr_001.md`, `[initiative]_us_001.md`, etc. (one file per story)

**ADF exclusion rule (applied first):**
Any interface prefixed with `ADF` (e.g. ADF108, ADF204) is completely ignored. These interfaces are owned by another team and must never produce a story. They are treated as background reference only.

**Splitting logic:**

| Scenario | Story type |
|---|---|
| New interface | Individual **User Story** — never grouped with other interfaces |
| Same change across multiple existing interfaces | One **CR** covering all |
| Multiple changes under the same logical feature for one interface | One **CR** |
| Different logical features or different change types | Separate **CRs** |

After story generation, the same review options are available as after the spec: conversational, automated, or both.

---

### Phase 3 — Validation (optional)

**Agent:** `ba-validator`

Reads all files in `output/specs/` and `output/stories/` and produces a structured validation report. Validation is **optional** — you can also review output conversationally with the agent instead of running the automated validator.

Rules run in two groups: **structural rules first** (Rules 9–14, BLOCKERs), then **content quality rules** (Rules 1–8).

**Structural rules (NEW — run first):**

| Rule | Severity | Description |
|---|---|---|
| Rule 9 — Spec template structure | BLOCKER | All 11 section headings present; tables have correct columns; no inline styles |
| Rule 10 — Protected section preservation | BLOCKER | SA-owned sections (Solution Overview, Involved Interfaces, Sequence Diagrams, Monitoring) still present and unmodified |
| Rule 11 — Required BA field population | BLOCKER / WARNING | All 7 BA-owned sections have substantive content, not just placeholders |
| Rule 12 — CR template compliance | BLOCKER | All required CR sections present; summary ≤10 words; BDD format with ≥2 scenarios |
| Rule 13 — User Story template compliance | BLOCKER | All required US sections present; summary ≤12 words; INT### format; BDD format with ≥3 scenarios |
| Rule 14 — Story structure consistency | BLOCKER / WARNING | No empty critical fields; no vague language in BDD criteria |

**Content quality rules (existing):**

| Rule | Severity | Description |
|---|---|---|
| Rule 1 — TO BE CONFIRMED still present | BLOCKER | Any field still containing a placeholder |
| Rule 2 — Vague acceptance criteria | WARNING | ACs without measurable outcomes, missing Given/When/Then structure, or no error/edge case coverage |
| Rule 3 — Missing documentation links | INFO | Documentation fields that are blank or missing |
| Rule 4 — ADF interfaces that slipped through | BLOCKER | Any story referencing an ADF-prefixed interface |
| Rule 5 — Inconsistent CR / User Story splits | BLOCKER | Wrong story type for an interface, or wrong grouping |
| Rule 6 — Missing system owner | WARNING | User Story with blank Users field, or CR with no owning system named |
| Rule 7 — Use Cases not referenced in test scenarios | WARNING | A Use Case with no corresponding test or acceptance criterion |
| Rule 8 — Business requirements without a story | INFO | A BR that cannot be traced to any generated story |

The report is saved to `output/validation/validation-report.md` with a structural and content breakdown.

---

### Phase 4 — Amendment

**Skill:** `/ba-amend`

Walks through every flag in the validation report one at a time (BLOCKERs first, then WARNINGs, then INFOs). For each flag you choose one of three options:

1. **Accept fix** — Claude applies the suggested fix automatically to the relevant file
2. **Edit manually** — you provide the replacement text and Claude applies it
3. **Skip** — the flag is left unresolved; you are warned if any BLOCKERs are skipped before publishing

After all flags are processed, a summary shows how many were applied, edited, and skipped.

---

### Phase 5 — Publish to Jira

**Agent:** `jira-publisher`

Updates an existing Jira ticket's description and acceptance criteria from a generated story file.

**Boundaries — strictly enforced:**
- Updates description and acceptance criteria fields **only**
- Never creates, deletes, or transitions tickets
- Never changes assignee, priority, labels, or any other field

**Process:**
1. You provide a Jira ticket key (e.g. `DTTP-1234`) and identify which story maps to it
2. The agent fetches the current ticket and reads the matching story block
3. The agent previews the description and acceptance criteria it will write
4. You confirm before any update is made
5. The agent updates the ticket and confirms the fields were written correctly

**Acceptance criteria format in Jira:**
Each scenario has a bold heading on its own line, followed by its Given / When / Then statements:

```
**Scenario 1: [scenario name]**
Given [precondition]
When [action]
Then [expected outcome]

**Scenario 2: [scenario name]**
Given [precondition]
When [action]
Then [expected outcome]
```

---

### Phase 6 — Publish to Confluence

**Agent:** `confluence-publisher`

Updates an existing Confluence page with the BA-owned sections from a generated spec. The page is always saved as a **draft** — you must review and publish manually in Confluence.

**Boundaries — strictly enforced:**
- Updates BA-owned sections only (see [Functional spec — sections and ownership](#functional-spec--sections-and-ownership) below)
- Never overwrites SA-owned sections
- Never creates, deletes, or publishes a page
- Always saves as draft

**Process:**
1. You provide a Confluence page URL and the spec file to use
2. The agent fetches the current page and extracts all SA-owned sections and Confluence macros verbatim
3. The agent assembles the updated page body: BA sections from the spec, SA sections preserved unchanged
4. A new Document History row is appended (author, date using the Confluence date macro, BA sections updated, status: Draft)
5. You confirm the update before it is submitted
6. The agent saves the draft and confirms

All URLs written to the page are rendered as clickable hyperlinks. All Confluence macros (TOC, PlantUML, status macros, whiteboard embeds, etc.) are preserved exactly as they appear on the current page.

The draft URL format is: `https://msccruises.atlassian.net/pages/resumedraft.action?draftId=[page_id]`

---

## Template validation

Template compliance is enforced automatically at two points in the pipeline — before any file is saved.

| When | What runs | What it checks |
|---|---|---|
| After spec generation | `knowledge/templates/spec_validator.py` | All 11 sections present, table column headers, user story format, no inline styles |
| After each story is generated | `knowledge/templates/story_validator.py --type=cr` or `--type=us` | Required sections, summary word count, BDD format, interface name format |

If a validator finds issues, the agent **auto-retries once** — regenerating the offending section with explicit template attention. If still failing after retry, the file is saved with a warning comment and the issue is surfaced in the next validation run.

You can also run the validators manually on any file:

```bash
# Validate a spec
python3 knowledge/templates/spec_validator.py output/specs/functional_spec_myfeature.html

# Validate a CR story
python3 knowledge/templates/story_validator.py --type=cr output/stories/myfeature_cr_001.md

# Validate a User Story
python3 knowledge/templates/story_validator.py --type=us output/stories/myfeature_us_001.md
```

Both validators output a JSON list of violations, or the string `OK` if compliant. Exit code `0` = valid, `1` = invalid.

---

## Story templates

Both templates are used consistently across the ba-story-generator and jira-publisher agents.

### Change Request (CR)

| Field | Description |
|---|---|
| Type | CR |
| Summary | Concise Jira-style title, max 10 words |
| Change Scope | Specific technical detail — which endpoint, field, method, or behaviour is changing |
| Rationale | Business reason — what problem this solves or value it delivers |
| **Resources** | |
| MuleSoft Requirements Page | Link if available in spec, otherwise blank |
| High Level Architecture Document | Link if available in spec, otherwise blank |
| API Documentation | Link if available in spec, otherwise blank |
| Confluence Page | Link if available in spec, otherwise blank |
| Acceptance Criteria (BDD) | Given / When / Then blocks — separate block per scenario, each scenario with a bold heading |

### User Story

| Field | Description |
|---|---|
| Type | User Story |
| Summary | Concise Jira-style title, max 12 words |
| User Story Statement | As a [persona] I want [goal] so that [benefit] |
| Interface Name | e.g. INT118 MyMSC: Web User Deactivation from Salesforce CRM |
| Purpose | What this API or interface does and who or what consumes it |
| Users | Consuming system or end user — e.g. MSC Agent via Salesforce, Logged-in B2C customer |
| Use Cases | Linked use cases or scenarios from the spec |
| **Functionality** | |
| Authentication | Authentication method required |
| Happy Path | Step-by-step main success flow |
| Alternative Paths | Alternative scenarios and expected behaviour |
| Error Scenarios | Error cases and expected system behaviour |
| **Documentation** | |
| MuleSoft Requirements Page | Link if available, otherwise blank |
| High Level Architecture Document | Link if available, otherwise blank |
| API Documentation | Link if available, otherwise blank |
| Specs | Link if available, otherwise blank |
| Acceptance Criteria (BDD) | Given / When / Then blocks — separate block per scenario, each scenario with a bold heading |

---

## Functional spec — sections and ownership

The functional specification has eleven sections. Seven are written by the BA agent; four are owned by the Solution Architect and are never modified by any BA agent or tool.

| # | Section | Owner | Scope |
|---|---|---|---|
| 1 | Document History | BA | Version, author, date, remarks, status, tickets |
| 2 | Reference Documentation | BA | Links to source documents, diagrams, and related pages |
| 3 | Feature Summary | BA | Overall solution — what it does, why it is needed, who benefits |
| 4 | Business Requirements | BA | Solution-level user stories (As a / I want / So that) — not API-specific |
| 5 | Use Cases | BA | End-to-end solution flows; names the MuleSoft API called in each |
| 6 | Solution Overview | **SA** | High-level architecture — **never overwritten by the BA agent** |
| 7 | Involved Interfaces | **SA** | Interface table — **never overwritten by the BA agent** |
| 8 | Sequence Diagrams | **SA** | PlantUML or embedded diagrams — **never overwritten by the BA agent** |
| 9 | Non-Functional Requirements | BA | API-specific: SLA, security, throughput, error handling, retry policy |
| 10 | Monitoring and Alerting Guidelines | **SA** | Alerting rules — **never overwritten by the BA agent** |
| 11 | Test Scenarios & Acceptance Criteria | BA | API-specific tests: HTTP method, endpoint, payload, status code, response body |

---

## Functional spec — writing standards

The following conventions are enforced by the agent and should be maintained during manual amendments:

| Section | Rule |
|---|---|
| Feature Summary | Business language only — no API names, field API names, interface IDs, or schema refs |
| Business Requirements | MuleSoft-relevant requirements only — exclude requirements owned by other systems (Salesforce, CDP, etc.) |
| NFRs | Scope to what is new or changed in this feature only — do not restate pre-existing requirements |
| Test Scenarios — Acceptance Criteria | MuleSoft interface behaviour only — what the interface accepts, rejects, forwards, or returns (including orchestration steps). Do not describe what downstream systems do with the data unless it is an error scenario |
| Document History — Tickets | Leave blank unless a ticket reference is explicitly provided |

---

## What gets produced

| Output | Location | Description |
|--------|----------|-------------|
| Preprocessed materials | `output/intake/*.md` | Structured markdown extracted from PDFs, meetings, Confluence pages |
| Functional specification | `output/specs/functional_spec_[name].html` | HTML spec ready for Confluence |
| BA stories | `output/stories/[initiative]_cr_001.md` etc. | Change Requests and User Stories as Markdown — one file per story |
| Validation report | `output/validation/validation-report.md` | Structural + content flags before publishing |
| Metrics | `output/metrics/metrics_[slug].json` | Per-feature timing, token usage, iteration counts |
| Weekly report | `output/metrics/weekly_reports/ba_metrics_[date].md` | Auto-generated Friday summary |

---

## Agents and skills

| File | Type | What it does | Invoked by |
|------|------|---|------------|
| `agents/intake-preprocessor.md` | Agent | Extracts PDFs (distill-doc), enriches meeting recordings (enrich-meeting), fetches Confluence pages | `/intake`, or via `ba-workflow` |
| `agents/functional-spec-generator.md` | Agent | Generates the HTML functional spec; reads template; validates structure before saving | `ba-workflow`, or directly |
| `agents/ba-story-generator.md` | Agent | Generates CRs and User Stories (from spec or direct input); validates each story before saving | `ba-workflow`, or directly |
| `agents/ba-validator.md` | Agent | Validates spec and stories — structural rules 9–14 first, then content rules 1–8 | `ba-workflow`, or directly |
| `agents/jira-publisher.md` | Agent | Updates description and acceptance criteria on existing Jira tickets | `ba-workflow`, or directly |
| `agents/confluence-publisher.md` | Agent | Updates BA sections on a Confluence page; always saves as draft | `ba-workflow`, or directly |
| `.claude/commands/ba-amend.md` | Skill | Interactive amendment tool — walks through validation flags one by one | `/ba-amend`, or via `ba-workflow` |
| `.claude/commands/ba-workflow.md` | Skill | Main orchestrator — presents the workflow menu and chains agents in order | `/ba-workflow` |
| `.claude/commands/intake.md` | Skill | Standalone intake preprocessing — PDFs, meetings, Confluence, text | `/intake` |
| `.claude/commands/ba-metrics.md` | Skill | Displays metrics summary with `--week`, `--detail`, `--csv`, `--trend` options | `/ba-metrics` |
| `.claude/commands/ba-metrics-report.md` | Skill | Generates weekly metrics report; also runs automatically every Friday at 5pm | `/ba-metrics-report` |

---

## Metrics tracking

Every workflow run writes a metrics JSON file to `output/metrics/`. Use the `/ba-metrics` command to view and export them.

```
/ba-metrics                    — summary table for all features
/ba-metrics --week             — this week's features only
/ba-metrics --detail [slug]    — full per-phase breakdown for one feature
/ba-metrics --csv              — export all metrics as CSV
/ba-metrics --trend            — show improvement trends over time
/ba-metrics-report             — generate the full weekly report on demand
```

A **weekly report** is generated automatically every **Friday at 5pm** (scheduled task) and saved to `output/metrics/weekly_reports/`. It covers iteration counts, template compliance rates, structural vs content fix ratios, and recommendations.

---

## Output folder structure

```
output/
├── intake/
│   ├── [source]_intake.md          ← preprocessed input materials
│   └── intake_summary.md           ← extraction summary
│
├── specs/
│   └── functional_spec_[name].html ← generated functional specification
│
├── stories/
│   ├── [initiative]_cr_001.md      ← Change Request (one file per story)
│   └── [initiative]_us_001.md      ← User Story (one file per story)
│
├── validation/
│   └── validation-report.md        ← structural + content flags
│
└── metrics/
    ├── metrics_[slug].json          ← per-feature metrics record
    └── weekly_reports/
        └── ba_metrics_[date].md    ← weekly summary report
```

---

## Reference documents

| Document | Location | Description |
|---|---|---|
| Setup guide | `docs/SETUP.md` | First-time environment setup |
| Capabilities overview | `docs/CAPABILITIES.md` | What the agent can and cannot do |
| MCP server guide | `mcp/README_MCP.md` | MCP server setup and tool reference |
| MSC context | `knowledge/MSC_CONTEXT.md` | Programme background, system glossary, rollout timeline |

---

## Key things to know

- **Missing information is never invented** — gaps are always marked `[TO BE CONFIRMED]` for you to fill in
- **Templates are read and enforced automatically** — agents read the HTML templates before generating output and validate structure before saving; structural issues are auto-retried once before surfacing a warning
- **Validation is optional** — you can review output conversationally with the agent instead of running automated validation; the workflow supports conversational, automated, or hybrid review at each phase
- **Stories are now Markdown files** (`.md`), one per story — easier to diff, edit, and convert for Jira
- **ADF interfaces are excluded from story generation** (e.g. ADF108) — this is by design; they are owned by another team
- **New interfaces always become User Stories** — existing interface changes always become CRs
- **Stories can be generated without a spec** — use the "direct input" option in ba-story-generator when you don't have a spec file
- **Confluence pages are always saved as drafts** — a human must review and publish manually
- **SA-owned sections are never touched** — Solution Overview, Involved Interfaces, Sequence Diagrams, and Monitoring & Alerting Guidelines are preserved exactly as the Solution Architect left them
- **All Confluence macros are preserved** — TOC, PlantUML, whiteboard embeds, and any other `ac:` macros are copied verbatim from the current page
- **Jira tickets are never created or deleted** — the agent only updates existing tickets you point it to; it never transitions status or changes assignee
- **Confluence page fetching** — the agent reads live Confluence pages via the MCP server when you provide a URL as input material; the MCP server must be running for this to work
- **Document History Tickets column** — left blank unless you explicitly provide a ticket reference

---

## Troubleshooting

**MCP server not starting — "uv: command not found"**
Use the full path to uv in Command Prompt or PowerShell:
```
%APPDATA%\Python\Python314\Scripts\uv.exe run msc-mcp-server
```

**Port 8080 already in use**
The MCP server from a previous session is still running — no action needed. If you need to restart it, close the previous terminal first.

**Claude is not responding to `/ba-workflow`**
Make sure you are in the correct project directory when you launch Claude Code:
```bash
cd "C:\Users\[your_user]\MSC_BA_Agent\MSC_BA_Agent"
codemie-claude
```

**Confluence or Jira errors (401 / 403)**
Your API token may have expired. Generate a new one at `https://id.atlassian.com/manage/api-tokens` and update `mcp/.env`. See `docs/SETUP.md` for details.

**Confluence draft is empty after publishing**
This happens when the HTML body is not correctly escaped in the API call. The agent uses Python `json.dump()` to avoid this — if it recurs, re-run the publish step.

**Output files look wrong or incomplete**
Run option **4 — Validate and publish** to get a validation report. It will flag exactly what needs to be fixed before publishing.
