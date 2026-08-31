# MSC Mule BA Agent — User Guide

An AI-assisted toolkit for Business Analysts on the MSC Cruises MuleSoft Integration team (DTTP programme). It takes raw input materials — emails, meeting notes, Confluence pages, Jira tickets, or pasted text — and walks you through the full BA pipeline: generating a functional specification, producing Jira-ready BA stories, validating quality, amending issues, and publishing to Jira and Confluence.

The agent never invents content. Any information it cannot find in your input materials is marked `[TO BE CONFIRMED]` for you to fill in.

---

## Contents

- [First-time setup](#first-time-setup)
- [Every session — start here](#every-session--start-here)
- [Running the BA workflow](#running-the-ba-workflow)
- [What to provide as input materials](#what-to-provide-as-input-materials)
- [Pipeline overview](#pipeline-overview)
- [Workflow phases in detail](#workflow-phases-in-detail)
  - [Phase 1 — Functional spec generation](#phase-1--functional-spec-generation)
  - [Phase 2 — BA story generation](#phase-2--ba-story-generation)
  - [Phase 3 — Validation](#phase-3--validation)
  - [Phase 4 — Amendment](#phase-4--amendment)
  - [Phase 5 — Publish to Jira](#phase-5--publish-to-jira)
  - [Phase 6 — Publish to Confluence](#phase-6--publish-to-confluence)
- [Story templates](#story-templates)
- [Functional spec — sections and ownership](#functional-spec--sections-and-ownership)
- [Functional spec — writing standards](#functional-spec--writing-standards)
- [What gets produced](#what-gets-produced)
- [Agents and skills](#agents-and-skills)
- [Output folder structure](#output-folder-structure)
- [Metrics tracking](#metrics-tracking)
- [Reference documents](#reference-documents)
- [Key things to know](#key-things-to-know)
- [Troubleshooting](#troubleshooting)

---

## First-time setup

Follow [`docs/SETUP.md`](docs/SETUP.md) once before using the agent for the first time. It covers installing Claude Code / Codemie, configuring your Atlassian API credentials, and starting the MCP server.

---

## Every session — start here

You need **two terminals** open each time you work.

**Terminal 1 — MCP server** (keep this running in the background):
```bash
cd mcp
uv run msc-mcp-server
```

You should see:
```
Starting MSC MCP Server on 0.0.0.0:8080 (transport=streamable-http)
Application startup complete.
```

If port 8080 is already in use, the server from a previous session is still running — you do not need to restart it.

**Terminal 2 — Claude Code** (this is where you work):
```bash
codemie-claude
```

> **Standard Claude Code fallback** (outside EPAM infrastructure):
> ```bash
> claude
> ```

---

## Running the BA workflow

Once Claude Code is open, type:

```
/ba-workflow
```

You will see a menu:

```
1. Spec only            — generate a functional spec from input materials
2. Stories only         — generate Jira BA stories (from spec or direct input)
3. Full end-to-end      — spec → stories → validate → amend → publish
4. Validate and publish — validate existing output and publish to Jira / Confluence
```

Choose the option that matches what you need. Claude will guide you through each step interactively.

**Option 2 — Stories only** offers two input modes:
- **From spec** — choose an existing spec file from `output/specs/` (or leave blank for the most recent)
- **Direct input** — provide interface names and requirements directly, without a spec file

You can also invoke any individual agent or skill directly — see [Agents and skills](#agents-and-skills) below.

---

## What to provide as input materials

When prompted for input materials, you can provide any combination of:

- **Pasted text** — copy and paste an email, Teams message, meeting notes, or requirements description directly into the chat
- **File paths** — e.g. `~/Documents/requirements.docx`
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
      ▼
┌─────────────────────────────┐
│  functional-spec-generator   │  → output/specs/functional_spec_<req-id>_[name].html
│  (agent)                     │    Sections: Document History, Reference Docs,
│                              │    Feature Summary, Business Requirements,
│                              │    Use Cases, NFRs, Test Scenarios & ACs
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  ba-story-generator          │  → output/stories/<req-id>-[slug]-cr-001.md
│  (agent)                     │    output/stories/<req-id>-[slug]-us-001.md
│                              │    One file per story. Applies ADF exclusion
│                              │    and splitting rules.
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  ba-validator                │  → output/validation/validation-report.md
│  (agent)                     │    Flags: TBC fields, vague ACs, missing links,
│                              │    ADF slippage, wrong splits, missing owners
└──────────────┬──────────────┘
               │
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

---

## Workflow phases in detail

### Phase 1 — Functional spec generation

**Agent:** `functional-spec-generator`

Reads all provided input materials and generates a structured HTML functional specification scoped to the MuleSoft team's deliverables.

The spec covers:
- The **overall solution** in the Feature Summary, Business Requirements, and Use Cases sections — giving developers and reviewers full business context
- The **API layer specifically** in the NFRs and Test Scenarios — written for the API(s) the MuleSoft team will build or change

**What the agent does:**
1. Asks for the requirement ID (`NEW-XXXX`) before proceeding
2. Reads all input materials (pasted text, files, Confluence pages, URLs)
3. Identifies the overall solution and the specific MuleSoft API(s) involved
4. Fills in all spec sections using the source materials
5. Marks gaps as `[TO BE CONFIRMED]` rather than inventing content
6. Saves the spec to `output/specs/functional_spec_<req-id>_[feature_name].html`
7. Reports the file path and all TO BE CONFIRMED fields found

For Test Scenarios, every Use Case must have at least one happy path test, one alternative path test, and one error scenario. Missing categories are flagged as gaps — never silently omitted.

---

### Phase 2 — BA story generation

**Agent:** `ba-story-generator`

Reads the functional spec (or direct input) and generates Jira-ready BA stories (Change Requests and User Stories), one file per story.

**ADF exclusion rule (applied first):**
Any interface prefixed with `ADF` (e.g. ADF108, ADF204) is completely ignored. These interfaces are owned by another team and must never produce a story.

**Splitting logic:**

| Scenario | Story type |
|---|---|
| New interface | Individual **User Story** — never grouped with other interfaces |
| Same change across multiple existing interfaces | One **CR** covering all |
| Multiple changes under the same logical feature for one interface | One **CR** |
| Different logical features or different change types | Separate **CRs** |

The agent reports:
- How many CRs and User Stories were generated
- Any ADF interfaces excluded
- Template compliance per story (Pass / issues found)
- The full path to each saved story file

**When invoked as Stories only (option 2)**, the agent stops after generation — no validation or publish prompt. Run option 4 when you are ready to validate and publish.

---

### Phase 3 — Validation

**Agent:** `ba-validator`

Reads all files in `output/specs/` and `output/stories/` and produces a structured validation report with flags at three severity levels.

**Validation rules:**

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

The report is saved to `output/validation/validation-report.md` with a summary count and the full list of flags in severity order.

---

### Phase 4 — Amendment

**Skill:** `/ba-amend`

Walks through every flag in the validation report one at a time (BLOCKERs first, then WARNINGs, then INFOs). For each flag you choose one of three options:

1. **Accept fix** — Claude applies the suggested fix automatically to the relevant file
2. **Edit manually** — you provide the replacement text and Claude applies it
3. **Skip** — the flag is left unresolved; you are warned if any BLOCKERs are skipped before publishing

After all flags are processed, a summary shows how many were applied, edited, and skipped — split by structural fixes (wrong story construction) and content fixes (missing or incomplete content).

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
2. The agent fetches the current ticket and reads the matching story file
3. The agent previews the description and acceptance criteria it will write
4. You confirm before any update is made
5. The agent updates the ticket and confirms the fields were written correctly

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
4. A new Document History row is appended (author, date, BA sections updated, status: Draft)
5. You confirm the update before it is submitted
6. The agent saves the draft and confirms

The draft URL format is: `https://msccruises.atlassian.net/pages/resumedraft.action?draftId=[page_id]`

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
| Acceptance Criteria (BDD) | Given / When / Then blocks — separate block per scenario, each with a bold heading |

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
| Acceptance Criteria (BDD) | Given / When / Then blocks — separate block per scenario, each with a bold heading |

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

| Section | Rule |
|---|---|
| Feature Summary | Business language only — no API names, field API names, interface IDs, or schema refs |
| Business Requirements | MuleSoft-relevant requirements only — exclude requirements owned by other systems (Salesforce, CDP, etc.) |
| NFRs | Scope to what is new or changed in this feature only — do not restate pre-existing requirements |
| Test Scenarios — Acceptance Criteria | MuleSoft interface behaviour only — what the interface accepts, rejects, forwards, or returns. Do not describe what downstream systems do with the data unless it is an error scenario |
| Document History — Tickets | Leave blank unless a ticket reference is explicitly provided |

---

## What gets produced

| Output | Location | Description |
|---|---|---|
| Functional specification | `output/specs/functional_spec_<req-id>_[name].html` | HTML spec ready for Confluence |
| BA stories | `output/stories/<req-id>-[slug]-cr-001.md` / `us-001.md` | One `.md` file per CR or User Story, ready for Jira |
| Validation report | `output/validation/validation-report.md` | Flags issues before publishing |
| Metrics record | `output/metrics/metrics_[slug].json` | Per-feature pipeline metrics |

---

## Agents and skills

| File | Type | What it does | Invoked by |
|---|---|---|---|
| `agents/functional-spec-generator.md` | Agent | Generates the HTML functional spec from raw input materials | `ba-workflow`, or directly |
| `agents/ba-story-generator.md` | Agent | Generates CRs and User Stories; applies ADF exclusion and splitting rules | `ba-workflow`, or directly |
| `agents/ba-validator.md` | Agent | Validates spec and stories; produces a flag report with BLOCKERs, WARNINGs, and INFOs | `ba-workflow`, or directly |
| `agents/jira-publisher.md` | Agent | Updates description and acceptance criteria on existing Jira tickets | `ba-workflow`, or directly |
| `agents/confluence-publisher.md` | Agent | Updates BA sections on a Confluence page; always saves as draft | `ba-workflow`, or directly |
| `.claude/commands/ba-workflow.md` | Skill | Main orchestrator — presents the workflow menu and chains agents in order | `/ba-workflow` |
| `.claude/commands/ba-amend.md` | Skill | Interactive amendment — walks through validation flags one by one | `/ba-amend`, or via `ba-workflow` |
| `.claude/commands/ba-metrics.md` | Skill | Displays pipeline metrics for all tracked features | `/ba-metrics` |
| `.claude/commands/ba-metrics-report.md` | Skill | Generates the weekly BA metrics report; runs automatically every Friday at 5pm | `/ba-metrics-report` |

---

## Output folder structure

```
output/
├── specs/
│   └── functional_spec_<req-id>_[feature_name].html   ← generated functional specification
│
├── stories/
│   ├── <req-id>-[slug]-cr-001.md                       ← one file per Change Request
│   └── <req-id>-[slug]-us-001.md                       ← one file per User Story
│
├── validation/
│   └── validation-report.md                            ← flags, severities, and suggested fixes
│
└── metrics/
    ├── metrics_[slug].json                              ← per-feature pipeline metrics
    ├── exports/
    │   └── metrics_export_[date].csv                   ← CSV export (/ba-metrics --csv)
    └── weekly_reports/
        └── weekly_report_[date].md                     ← Friday metrics report
```

> `output/` is excluded from version control — it is never committed to the repository.

---

## Metrics tracking

Every feature processed through `/ba-workflow` is automatically tracked. Metrics are written to `output/metrics/metrics_[slug].json` at each phase boundary and updated in real time via PostToolUse hooks.

**Tracked fields include:** requirement ID, session duration, per-phase iterations, CR/US counts, structural vs content violation split, template compliance rate, feedback loops, and Jira/Confluence publish targets.

### Metrics commands

| Command | Description |
|---|---|
| `/ba-metrics` | Summary table for all features |
| `/ba-metrics --week` | This week's features only (Mon–Fri 6pm cutoff) |
| `/ba-metrics --detail [slug]` | Full per-phase breakdown for one feature |
| `/ba-metrics --csv` | Export all metrics to `output/metrics/exports/` |
| `/ba-metrics --trend` | Improvement trends across all features |
| `/ba-metrics-report` | Generate the weekly report (also runs automatically every Friday at 5pm) |

**Template compliance** is calculated as: `1 − (structural fixes / total fixes)` across all amendment runs. A structural fix is one that corrects wrong story construction (wrong CR/US type, ADF slippage, wrong splits); a content fix is one that resolves missing or incomplete content.

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
- **ADF interfaces are excluded from story generation** (e.g. ADF108) — this is by design; they are owned by another team
- **New interfaces always become User Stories** — existing interface changes always become CRs
- **Stories are saved as individual `.md` files**, one per CR or User Story, named with the requirement ID prefix
- **Confluence pages are always saved as drafts** — a human must review and publish manually
- **SA-owned sections are never touched** — Solution Overview, Involved Interfaces, Sequence Diagrams, and Monitoring & Alerting Guidelines are preserved exactly as the Solution Architect left them
- **Jira tickets are never created or deleted** — the agent only updates existing tickets you point it to; it never transitions status or changes assignee
- **Metrics are written automatically** — no manual prompting needed; the PostToolUse hook updates the metrics JSON whenever a key file is written or a publish tool fires

---

## Troubleshooting

**MCP server not starting — "uv: command not found"**
Ensure `uv` is installed and on your PATH. See `docs/SETUP.md` for installation instructions.

**Port 8080 already in use**
The MCP server from a previous session is still running — no action needed. If you need to restart it, close the previous terminal first.

**Claude is not responding to `/ba-workflow`**
Make sure you are in the correct project directory when you launch Claude Code:
```bash
cd /path/to/MSC--BA-agent
codemie-claude
```

**Confluence or Jira errors (401 / 403)**
Your API token may have expired. Generate a new one at `https://id.atlassian.com/manage/api-tokens` and update `mcp/.env`. See `docs/SETUP.md` for details.

**Confluence draft is empty after publishing**
The agent uses Python `json.dump()` to avoid HTML escaping issues — if it recurs, re-run the publish step.

**Output files look wrong or incomplete**
Run option **4 — Validate and publish** to get a validation report. It will flag exactly what needs to be fixed before publishing.

**Metrics file not updating**
The PostToolUse hook requires `python3` to be on your PATH. Run `python3 --version` to verify. If the hook fails silently, the metrics bash blocks in `ba-workflow.md` can be run manually to backfill the data.
