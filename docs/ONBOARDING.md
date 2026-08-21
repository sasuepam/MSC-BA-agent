# BA Agent — Onboarding Guide

**Who this is for:** A new Business Analyst joining the MSC Cruises EINT team and picking up the BA Agent for the first time.

**What you'll walk away knowing:** What the tool is, how to install it, how to run a full feature workflow from raw input to published Jira and Confluence artefacts, how to read your metrics, and a library of copy-paste prompts for common scenarios.

---

## Table of Contents

1. [What Is the BA Agent?](#1-what-is-the-ba-agent)
2. [What It Does and Doesn't Do](#2-what-it-does-and-doesnt-do)
3. [The Workflow at a Glance](#3-the-workflow-at-a-glance)
4. [Prerequisites](#4-prerequisites)
5. [Installation](#5-installation)
6. [Daily Startup](#6-daily-startup)
7. [Running a Feature — Step by Step](#7-running-a-feature--step-by-step)
   - [Phase 0: Intake (Optional)](#70-phase-intake-optional)
   - [Phase: Spec](#71-phase-spec)
   - [Phase: Stories](#72-phase-stories)
   - [Phase: Validate (Optional)](#73-phase-validate-optional)
   - [Phase: Amend](#74-phase-amend)
   - [Phase: Publish](#75-phase-publish)
8. [All Slash Commands](#8-all-slash-commands)
9. [Understanding the Outputs](#9-understanding-the-outputs)
10. [Metrics — Tracking Your Work](#10-metrics--tracking-your-work)
11. [Reusable Prompts](#11-reusable-prompts)
12. [Tips and Best Practices](#12-tips-and-best-practices)
13. [Troubleshooting](#13-troubleshooting)
14. [Glossary](#14-glossary)

---

## 1. What Is the BA Agent?

The BA Agent is an AI-assisted toolkit that turns raw input — emails, meeting notes, PDFs, meeting recordings, Confluence pages, Jira tickets, sequence diagrams — into structured BA documentation ready for development.

It runs entirely inside **Codemie**, EPAM's internal deployment of Claude. This matters for two reasons:

- All client data stays inside EPAM's tenant. **Never use the public `claude` or `claude-code` CLI with MSC data.**
- The agent has access to MSC's Jira and Confluence through a local MCP server you run on your machine.

The agent is opinionated about the MSC MuleSoft integration context. It knows the DTTP programme, the ADF exclusion rule, the 11-section functional spec format, the exact CR/US splitting rules, and the template structure for all artefact types. It enforces these rules automatically — validating each artefact's structure before saving and running quality checks on demand.

---

## 2. What It Does and Doesn't Do

### It does

| Capability | Detail |
|---|---|
| Preprocess raw input materials | Extract PDFs, enrich meeting recordings, fetch Confluence pages — structures everything into clean Markdown before spec generation |
| Generate functional specs | 11-section HTML spec from any combination of input materials; reads the spec template before generating; validates structure before saving |
| Generate Change Requests | One CR per logical change across one or many existing interfaces; validates against CR template before saving; output as individual `.md` files |
| Generate User Stories | One US per new interface introduced; validates against US template before saving; output as individual `.md` files |
| Accept direct requirements input | Generate stories from a list of interfaces and requirements — no spec file needed |
| Validate artefacts | 14 rules in two groups: structural rules 9–14 (template compliance) run first; content quality rules 1–8 run after. Optional — conversational, automated, or both |
| Amend artefacts interactively | Walk through every validation flag; apply, edit, or skip each one; distinguishes structural vs content fixes |
| Publish to Jira | Update description and acceptance criteria on existing tickets only |
| Publish to Confluence | Update BA sections of a spec page, always saving as draft |
| Track metrics | Time per phase, template auto/manual fix counts, iteration counts, structural vs content violations, token usage, cost per feature |
| Weekly metrics reports | Auto-generated every Friday at 5pm GMT+1; also available on demand with `/ba-metrics-report` |

### It doesn't

- Invent content. Any information it cannot find in your source materials is marked `[TO BE CONFIRMED]`.
- Create Jira tickets. It only updates existing ones.
- Create or delete Confluence pages. It only updates the BA sections of an existing page.
- Touch SA-owned sections of a spec (Solution Overview, Involved Interfaces, Sequence Diagrams, Monitoring and Alerting Guidelines).
- Generate stories for ADF-prefixed interfaces (ADF108, ADF204, etc.). Those belong to another team.
- Write directly to production Confluence without an explicit confirmation step.

---

## 3. The Workflow at a Glance

```
Input materials
(PDF / meeting recording / email / notes / Confluence URL / Jira URL)
        │
        ▼
[PHASE 0: INTAKE] ──► output/intake/[source]_intake.md    ← optional
        │                           intake_summary.md
        ▼
  [PHASE: SPEC]   ──► output/specs/functional_spec_[feature].html
        │                  (template read + pre-save validation)
        │
        │  Choose review mode:
        │  Conversational / Automated / Both / Skip
        ▼
[PHASE: STORIES]  ──► output/stories/[feature]_cr_001.md  ← one .md per story
        │              output/stories/[feature]_us_001.md
        │                  (template read + per-story validation)
        │
        │  Choose review mode:
        │  Conversational / Automated / Both / Skip
        ▼
[PHASE: VALIDATE] ──► output/validation/validation-report.md   ← optional
        │                  Rules 9–14 (structural) first
        │                  Rules 1–8 (content quality) after
        │
   BLOCKERs? ──Yes──► [PHASE: AMEND] ──► re-validate
        │ No
        ▼
[PHASE: PUBLISH]  ──► Jira ticket descriptions + Confluence draft page
        │
        ▼
   output/metrics/metrics_[feature].json
   output/metrics/weekly_reports/   ← auto-generated Fridays at 5pm
```

You can run each phase individually, or use the full end-to-end option to chain them automatically.

---

## 4. Prerequisites

Before installation, check you have all four of these:

| Requirement | Check | Install if missing |
|---|---|---|
| **Git** | `git --version` | https://git-scm.com |
| **Python 3.12+** | `python3 --version` | https://python.org |
| **uv** (Python package manager) | `uv --version` | `pip install uv` |
| **Codemie** | `codemie-claude --version` | Ask your team lead — it's an internal EPAM tool |

You also need an **Atlassian API token** for MSC Jira and Confluence. Generate one at: `https://id.atlassian.com/manage-profile/security/api-tokens`. One token covers both Jira and Confluence.

---

## 5. Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/sasuepam/MSC-BA-agent.git
cd MSC-BA-agent
```

### Step 2 — Run the setup wizard

Open Codemie from the project root and run the setup command:

```bash
codemie-claude
```

Once Codemie loads, type:

```
/setup
```

The wizard will ask you for:

- Your Confluence URL (e.g. `https://msccruises.atlassian.net`)
- Your Atlassian email address
- Your Atlassian API token
- Whether to configure a sandbox instance (recommended — lets you test without touching production)
- Your Jira URL and credentials (usually the same as Confluence)
- An MCP port (default is 8080; keep the default unless something else is already using that port)

It writes these to `mcp/.env`, installs Python dependencies via `uv sync`, and registers the MCP server with Codemie.

### Step 3 — Start the MCP server (Terminal 1)

Open a **separate terminal window** and keep it running throughout your session:

```bash
cd mcp
uv run msc-mcp-server
```

You should see output confirming the server is listening on port 8080. Leave this window open.

### Step 4 — Verify the setup

Back in your Codemie terminal, run:

```
/setup verify
```

This pings the MCP server, checks all configured integrations are reachable, and prints a ready summary. If anything fails, see the [Troubleshooting](#13-troubleshooting) section.

---

## 6. Daily Startup

Every time you start a session:

**Terminal 1 — start the MCP server:**
```bash
cd MSC-BA-agent/mcp
uv run msc-mcp-server
```

**Terminal 2 — open Codemie:**
```bash
cd MSC-BA-agent
codemie-claude
```

Then type `/ba-workflow` to begin.

That's it. The MCP server handles all Jira and Confluence calls automatically in the background.

---

## 7. Running a Feature — Step by Step

Type `/ba-workflow` and you'll see a menu:

```
1. Generate functional spec only
2. Generate stories (from spec or direct input)
3. Full end-to-end (spec → stories → validate → amend → publish)
4. Validate and publish existing artefacts
```

**Choice 3** is the most common for a new feature. **Choice 4** is for returning to work you started in a previous session.

---

### 7.0 Phase: Intake (Optional)

Before generating the spec, the workflow asks: *"Would you like to preprocess your input materials first?"*

**When to say yes:** Your input materials are PDFs, meeting recordings, or Confluence pages that need extracting before the agent can read them properly.

**When to say no (or skip):** You're pasting text directly, or your materials are already clean Markdown/text files.

You can also run intake at any time independently with `/intake`.

**What it accepts:**

| Input type | What you provide |
|---|---|
| PDF files | File path (e.g. `docs/requirements.pdf`) |
| Meeting recordings | VTT transcript path + video file path |
| Confluence pages | Full page URL |
| Plain text | Paste directly at the prompt |

**What it produces:** `output/intake/[source]_intake.md` for each input, plus `output/intake/intake_summary.md` listing key topics extracted. These files are automatically passed to the spec generator.

---

### 7.1 Phase: Spec

The spec phase invokes the `functional-spec-generator` agent. You provide your input materials at the prompt (or they are read from `output/intake/` if the intake phase ran).

**What it produces:** `output/specs/functional_spec_[feature_name].html`

The spec has 11 sections. The agent reads the spec template first, then fills the 7 BA-owned sections from your materials and leaves the 4 SA-owned sections as placeholders.

**BA-owned sections (agent fills these):**
- Document History
- Reference Documentation
- Feature Summary
- Business Requirements (`As a [actor] I want [action] so that [benefit]` format)
- Use Cases (numbered UC-001 onwards, naming the responsible MuleSoft API)
- Non-Functional Requirements (numbered NFR-001 onwards)
- Test Scenarios & Acceptance Criteria

**SA-owned sections (never touched by the agent):**
- Solution Overview
- Involved Interfaces
- Sequence Diagrams
- Monitoring and Alerting Guidelines

**Template validation:** Before saving, the agent runs `spec_validator.py` to check structure (all 11 sections present, table column headers correct, Business Requirements in user story format, no inline CSS). If issues are found it auto-retries once; if still failing after retry the file is saved with a warning and flagged in the next validation run.

**What to provide as input:**
- Paste raw text directly (email content, meeting notes, requirements)
- Give a file path: `docs/my_requirements.txt`
- Give a Confluence URL: the agent will read the page
- Give a Jira URL: the agent will read the ticket description
- Give multiple at once — the agent correlates across all sources

**What you get back:**
- The saved file path
- A list of all `[TO BE CONFIRMED]` fields
- Template validation result (PASS or violation count)

**Tip:** More input is always better. Paste the full email thread, not just the summary. The agent never makes things up; it can only work with what you give it.

**After the spec is saved**, the agent asks how you'd like to review it:

- **Conversational** — ask the agent to fix issues directly in chat
- **Automated** — run `ba-validator` with structural rules (Rules 9–11) against the spec
- **Both** — conversational first, then automated as a final check
- **Skip** — move straight to stories

---

### 7.2 Phase: Stories

The stories phase invokes the `ba-story-generator` agent.

**What it produces:** Individual `.md` files, one per story — e.g. `output/stories/[feature]_cr_001.md`, `[feature]_us_001.md`

**Two input modes:**

| Mode | When to use | How to trigger |
|---|---|---|
| **From spec** | Read the functional spec from `output/specs/` and derive stories from it | Default — just confirm when asked |
| **Direct input** | Provide a list of interfaces and requirements directly — no spec file needed | Useful for quick stories without a full spec |

**CR vs US — the splitting rule:**

| Situation | Output |
|---|---|
| Existing interface being changed | Change Request (CR) |
| New interface being introduced | User Story (US) — one per interface |
| Same change across multiple existing interfaces | One CR covering all |
| Multiple different changes under the same feature | Separate CRs per change type |
| ADF-prefixed interface | Excluded — not produced at all |

**Template validation:** Before saving each story, the agent runs `story_validator.py` to check structure (required sections, summary length, BDD format, interface naming). It auto-retries once on failure; if still failing the story is saved with a warning.

**What you get back:**
- CR count and US count
- A list of any ADF interfaces that were excluded
- Template validation result per story (PASS or violation count)

**After stories are saved**, the agent asks how you'd like to review them (same four options: conversational / automated / both / skip).

---

### 7.3 Phase: Validate (Optional)

Validation is optional. The `ba-validator` agent reads all files in `output/specs/` and `output/stories/`.

**What it produces:** `output/validation/validation-report.md`

**Fourteen rules in two groups — structural rules run first:**

#### Structural rules (Rules 9–14) — run first

| Rule | Severity | What it checks |
|---|---|---|
| Rule 9 — Spec template structure | BLOCKER | All 11 sections present; table columns correct; no inline CSS |
| Rule 10 — Protected section preservation | BLOCKER | SA-owned sections present and unmodified |
| Rule 11 — Required BA field population | BLOCKER / WARNING | All 7 BA sections have substantive content |
| Rule 12 — CR template compliance | BLOCKER | Required CR sections, summary ≤10 words, BDD ≥2 scenarios |
| Rule 13 — US template compliance | BLOCKER | Required US sections, summary ≤12 words, INT### format, BDD ≥3 scenarios |
| Rule 14 — Story structure consistency | BLOCKER / WARNING | No empty critical fields; no vague BDD language |

#### Content quality rules (Rules 1–8) — run after structural checks

| Rule | Severity | What it checks |
|---|---|---|
| Rule 1 — TBC fields | BLOCKER | Any `[TO BE CONFIRMED]` still present |
| Rule 2 — Vague ACs | WARNING | Acceptance Criteria missing Given/When/Then or measurable outcome |
| Rule 3 — Missing doc links | INFO | Blank Confluence/API doc/HLA fields |
| Rule 4 — ADF slippage | BLOCKER | ADF-prefixed interface found in any story |
| Rule 5 — Wrong CR/US splits | BLOCKER | New interface given a CR, or existing change given a US |
| Rule 6 — No system owner | WARNING | Users field blank or Change Scope missing owning system |
| Rule 7 — Untested use cases | WARNING | Use case IDs in spec with no matching test scenario |
| Rule 8 — Uncovered BRs | INFO | Business requirements with no traceable story |

The validation report has separate tables for structural and content violations. Structural BLOCKERs must be resolved before content rules are considered.

---

### 7.4 Phase: Amend

When BLOCKERs are found, the workflow automatically moves to the amend phase. You can also run it manually with `/ba-amend`.

The agent reads the validation report and walks you through every flag in severity order (structural BLOCKERs first, then content BLOCKERs, then WARNINGs, then INFOs).

For each flag, you choose:

- **Accept fix** — Claude applies the suggested edit directly to the file
- **Edit manually** — you provide the replacement text, Claude applies it
- **Skip** — flag stays unresolved (you'll be warned before publishing if it's a BLOCKER)

After all flags are handled, you get an Amendment Summary showing Applied / Edited / Skipped counts broken down into structural fixes and content fixes, plus a list of which files were modified.

---

### 7.5 Phase: Publish

After validation passes (zero BLOCKERs), you choose where to publish:

**Option A — Jira only:** Provide one or more ticket keys (e.g. `DTTP25-1234`). The agent reads the matching story `.md` file, shows you a preview of the description and acceptance criteria, asks for confirmation, then updates the ticket.

**Option B — Confluence only:** Provide the page URL. The agent fetches the current page, replaces only the BA sections with content from `output/specs/`, preserves all SA sections exactly, adds a Document History row, and saves as a draft.

**Option C — Both:** Runs Jira first, then Confluence.

**Option D — Skip publishing:** Closes out the workflow and saves metrics without publishing.

**Important:** Confluence pages are always saved as **drafts**. You must open the page and publish it manually after reviewing.

After publishing, the agent asks you to run `/cost` and enter the token and cost values — these are saved to your metrics file.

---

## 8. All Slash Commands

| Command | What it does | When to use |
|---|---|---|
| `/ba-workflow` | Main entry point — presents the 4-option menu | Start of every feature session |
| `/intake` | Standalone intake preprocessing — PDFs, recordings, Confluence pages, text | Before spec generation, or any time you need to preprocess raw materials |
| `/ba-amend` | Interactive flag resolution | Manually re-run amendments, or when called by `/ba-workflow` |
| `/ba-metrics` | Summary table of all tracked features | Review your output at any time |
| `/ba-metrics --week` | This week's features only (Monday–today) | Monday morning review |
| `/ba-metrics --detail [slug]` | Per-phase breakdown for one feature | Deep dive on a single feature |
| `/ba-metrics --csv` | Export all metrics as CSV to `output/metrics/metrics_export.csv` | Reporting or spreadsheet analysis |
| `/ba-metrics --trend` | Improvement trends over time (feedback loops, structural fix ratio) | Team health check |
| `/ba-metrics-report` | Generate the full weekly report on demand | Ad hoc reporting; also auto-runs Fridays at 5pm |
| `/setup` | First-time setup wizard | First install only, or to update credentials |
| `/setup verify` | Ping MCP server and check all integrations | After install, or when troubleshooting connectivity |

---

## 9. Understanding the Outputs

```
output/
├── intake/
│   ├── [source]_intake.md          ← preprocessed input (one file per source)
│   └── intake_summary.md           ← extraction summary and key topics
│
├── specs/
│   └── functional_spec_[feature_name].html   ← 11-section spec, plain HTML
│
├── stories/
│   ├── [feature]_cr_001.md         ← Change Request (one file per story)
│   ├── [feature]_cr_002.md
│   └── [feature]_us_001.md         ← User Story (one file per story)
│
├── validation/
│   └── validation-report.md        ← Flag list with severities; structural first
│
└── metrics/
    ├── metrics_[feature_slug].json  ← Timing, tokens, cost, fix counts
    └── weekly_reports/
        └── ba_metrics_[date].md    ← Weekly summary (auto-generated Fridays)
```

**Spec files** are plain HTML with no embedded CSS. They're designed to paste cleanly into Confluence. Tables use `border="1" cellpadding="5" cellspacing="0"` and nothing else.

**Story files** are individual Markdown files — one per CR or User Story — named `[feature]_cr_001.md`, `[feature]_us_001.md`, etc. This makes it easy to publish individual stories to Jira without opening a combined file.

**Validation reports** are Markdown. Each flag is a block with: FLAG-NNN, rule number, severity, file, section, description of the issue, and a suggested fix. Structural flags (Rules 9–14) appear before content flags (Rules 1–8).

**Metrics files** are JSON. Use `/ba-metrics` and its subcommands to read them — you don't need to open the JSON directly.

---

## 10. Metrics — Tracking Your Work

Every feature run automatically creates `output/metrics/metrics_[slug].json`. This file tracks:

- Session start and end timestamps
- Total session duration in minutes
- Whether intake preprocessing was used
- Validation mode chosen (conversational / automated / both / skipped)
- Per-phase timestamps, durations, and iteration counts
- Template auto-fix counts (how many times the validator triggered an auto-retry) and manual-fix counts
- Validation run history (structural blocker/warning counts + content blocker/warning/info counts per run)
- Amend run history (structural fixes, content fixes, applied/edited/skipped per run)
- Feedback loop count (incremented each time you amend and re-validate)
- Jira tickets updated and Confluence page URL
- Token usage (input, output, total) and estimated cost in USD

**To see a summary across all features:**

```
/ba-metrics
```

Output: table with slug, status, total time, feedback loops, tokens, cost.

**To filter to this week's work:**

```
/ba-metrics --week
```

**To see per-phase detail for one feature:**

```
/ba-metrics --detail free_balcony_upgrade
```

**To export everything as a CSV:**

```
/ba-metrics --csv
```

Saves to `output/metrics/metrics_export.csv`.

**To see improvement trends across features:**

```
/ba-metrics --trend
```

Shows feedback loops per feature and structural fix ratio over time (target: <10% structural). Useful for identifying whether template validation is reducing rework.

**Weekly report:** Every Friday at 5pm GMT+1, a weekly summary is automatically generated at `output/metrics/weekly_reports/ba_metrics_[date].md`. To generate one on demand:

```
/ba-metrics-report
```

**Entering token and cost data:** After publishing, the agent asks you to run `/cost` in a separate message. This shows you the token counts for the session. Enter those values when the agent prompts — they're saved to the metrics file.

---

## 11. Reusable Prompts

Copy these into your Codemie session as needed.

---

### Starting a workflow

**From an email thread (paste directly):**
```
/ba-workflow

[paste the full email thread content here]
```

**From a Confluence page:**
```
/ba-workflow

The requirements are documented at: https://msccruises.atlassian.net/wiki/spaces/DTTP/pages/[page-id]/[page-title]
```

**From a Jira epic:**
```
/ba-workflow

The feature is described in: https://msccruises.atlassian.net/browse/DTTP25-[number]
```

**From multiple sources:**
```
/ba-workflow

Requirements: https://msccruises.atlassian.net/wiki/spaces/DTTP/pages/[id]/[title]
Additional context from stakeholder email: [paste email here]
Sequence diagram: [paste or attach image]
```

**Spec only, no stories yet:**
```
/ba-workflow
1

[your input materials]
```

---

### Intake phase prompts

**Run intake on a PDF before starting the workflow:**
```
/intake

PDF: docs/requirements_[feature].pdf
```

**Run intake on a meeting recording:**
```
/intake

VTT: recordings/[meeting].vtt
Video: recordings/[meeting].mp4
```

**Run intake on a Confluence page:**
```
/intake

Confluence page: https://msccruises.atlassian.net/wiki/spaces/DTTP/pages/[id]/[title]
```

**Run intake on multiple sources at once:**
```
/intake

PDF: docs/requirements.pdf
VTT: recordings/kickoff.vtt
Video: recordings/kickoff.mp4
Confluence: https://msccruises.atlassian.net/wiki/spaces/DTTP/pages/[id]/[title]
```

---

### Spec phase prompts

**Filling in a TBC field:**
```
The [field name] should be: [your value]. Please update the spec and replace that [TO BE CONFIRMED] marker.
```

**Adding a business requirement you forgot:**
```
Please add a business requirement to the spec: "The system must [requirement text]." Add it under Section 4 as BR-[next number].
```

**Correcting a use case:**
```
Use case UC-[number] has the wrong trigger condition. It should be: [correct trigger]. Please update it.
```

**Requesting all TBC fields listed:**
```
List all [TO BE CONFIRMED] markers currently in the spec with the section and field name for each.
```

---

### Stories phase prompts

**Generate stories with direct input (no spec):**
```
/ba-workflow
2

I want to generate stories without a spec. The interfaces are:
- INT[number] — [interface name] (new interface)
- INT[number] — [interface name] (existing, being modified to add [change description])

Business requirements:
1. [requirement text]
2. [requirement text]
```

**Checking story split decisions:**
```
Walk me through why each interface was given a CR versus a US.
```

**Querying an excluded interface:**
```
INT[number] was excluded from the stories. Can you confirm whether it was ADF-prefixed or explain why?
```

**Requesting a standalone story for one interface:**
```
Generate the story for INT[number] only and save it as a new .md file in output/stories/.
```

---

### Validation phase prompts

**Running validation manually:**
```
Run validation on the current spec and stories files.
```

**Checking only for structural BLOCKERs:**
```
Run validation — structural rules only (Rules 9–14). I'll handle content quality later.
```

**Checking only for content BLOCKERs:**
```
Run validation — content quality rules only (Rules 1–8). Structural checks already passed.
```

**Re-running validation after amendments:**
```
Re-run validation on the updated files. I want to confirm the BLOCKERs from the last run are resolved.
```

---

### Amendment phase prompts

**Running amendments manually:**
```
/ba-amend
```

**Fixing a specific flag:**
```
Fix FLAG-[number] from the validation report. Apply the suggested fix.
```

**Accepting all INFO-level flags at once:**
```
Accept the suggested fix for all INFO-level flags without asking me to confirm each one.
```

**Providing manual text for a TBC field:**
```
For FLAG-[number], the correct value is: [your text]. Please apply that edit.
```

---

### Publish phase prompts

**Publishing to a Jira ticket:**
```
Publish the stories to Jira ticket DTTP25-[number].
```

**Publishing multiple tickets at once:**
```
Publish the stories to Jira tickets DTTP25-[number], DTTP25-[number], DTTP25-[number].
```

**Publishing to Confluence:**
```
Publish the spec to the Confluence page at: https://msccruises.atlassian.net/wiki/spaces/DTTP/pages/[id]/[title]
```

**Previewing before publishing:**
```
Show me a preview of what the Jira description will look like for DTTP25-[number] before updating it.
```

---

### Working with existing artefacts

**Resuming a previous session:**
```
/ba-workflow
4
```

**Loading a specific spec file:**
```
Generate stories from output/specs/functional_spec_[feature_name].html
```

**Comparing two spec versions:**
```
Read output/specs/functional_spec_[feature_name].html and output/specs/functional_spec_[feature_name]_v2.html. Summarise the differences between them.
```

---

### Metrics prompts

**Summary of all features:**
```
/ba-metrics
```

**This week's features only:**
```
/ba-metrics --week
```

**Detailed view of one feature:**
```
/ba-metrics --detail [feature_slug]
```

**Export to CSV:**
```
/ba-metrics --csv
```

**See trend data:**
```
/ba-metrics --trend
```

**Generate weekly report now:**
```
/ba-metrics-report
```

**Listing features with unresolved TBCs:**
```
/ba-metrics

Which of these features still have status "in_progress"?
```

---

## 12. Tips and Best Practices

**Give the agent everything, not just the summary.** The agent can only work from what you provide. A full email thread is better than a paraphrase. A Confluence page URL is better than a description of what's on the page.

**Use intake for PDFs and meeting recordings.** If your input is a PDF or a `.vtt` meeting transcript, run `/intake` first. The intake phase produces a clean, structured Markdown file that the spec generator can read much more reliably than a raw binary.

**Resolve TBCs before generating stories.** Stories inherit TBC fields from the spec, which will then become BLOCKERs in validation. It's faster to fill in TBCs in the spec first.

**Template auto-fixes are your early warning system.** If the agent auto-retried the template validator during spec or story generation, there were structural issues caught early. Check the template compliance result reported after each phase — a clean PASS means your artefacts match the expected structure before anyone else sees them.

**Choose your validation mode deliberately.** After spec and story generation the agent asks how you'd like to review. "Conversational" is faster for small features you know well. "Automated" catches blind spots you might miss. "Both" is the safest option for complex features or when a spec goes to a new SA.

**Use the sandbox Confluence instance for experiments.** Your `mcp/.env` can have a separate sandbox URL. When the agent asks which instance to publish to, choose sandbox until you're confident in the output.

**Re-validate after every amendment session.** The amend phase can resolve some flags while introducing edge cases. A quick re-validation confirms you're clean.

**Watch the structural fix ratio in trends.** `/ba-metrics --trend` shows what percentage of amendments were structural (template) fixes vs content fixes. A high structural ratio means artefacts are not meeting the template even after pre-save validation — which may indicate ambiguous or minimal input materials.

**Don't close the MCP server terminal mid-session.** If the server stops, publish operations will fail. Keep Terminal 1 open for the duration of your session.

**One feature = one session.** The metrics file tracks one slug from start to finish. If you close Codemie mid-feature and restart, use option 4 in `/ba-workflow` ("Validate and publish existing artefacts") to resume — it will load the existing metrics file for that slug.

**Check the Document History before publishing to Confluence.** The agent adds a row automatically, but it's worth reviewing that the version number, sections updated, and date look correct before the SA publishes the draft.

**For ADF interfaces, check the story count.** After stories are generated, verify the ADF exclusion list matches what you expected. If a non-ADF interface was accidentally excluded, flag it before publishing.

---

## 13. Troubleshooting

**`/setup verify` fails on Confluence or Jira connectivity**
- Check `mcp/.env` — confirm the URL, email, and token are correct
- Confirm the MCP server is running in Terminal 1 (`uv run msc-mcp-server`)
- Make sure your API token hasn't expired at `https://id.atlassian.com/manage-profile/security/api-tokens`

**"MCP server not found" or tool calls failing**
- Re-register the MCP server: `codemie-claude mcp add msc-ba --transport http http://localhost:8080/mcp`
- Restart Codemie after re-registering

**MCP server port already in use**
- Check if something is already on port 8080: `lsof -i :8080`
- Change the port in `mcp/.env` (`MSC_PORT=8081`) and re-register with the new URL

**Confluence page update blocked with "production write lock"**
- This is a safety block. The agent is preventing a write to the production Confluence space without explicit confirmation
- When the agent asks for confirmation, type the exact phrase: `YES PUBLISH TO PRODUCTION`

**Spec or story file not found in output/**
- Check the agent's last message — it always reports the saved file path
- Confirm the MCP server was running when the agent tried to write (Write tool doesn't need MCP, but if there was an earlier error the file may not have been created)
- Try running the spec or stories phase again: `/ba-workflow` → option 1 or 2

**`spec_validator.py` or `story_validator.py` not found**
- Confirm you are running from the project root (`MSC-BA-agent/`)
- The validators live at `knowledge/templates/spec_validator.py` and `knowledge/templates/story_validator.py`
- Run manually to check: `python3 knowledge/templates/spec_validator.py output/specs/functional_spec_[name].html`

**Stories not generating as separate `.md` files**
- If you have stories from before the August 2026 update, they may be in the old combined HTML format
- Re-run stories generation: `/ba-workflow` → option 2 — it will produce the new per-story `.md` files

**[TO BE CONFIRMED] fields are still in the published output**
- Validation Rule 1 (BLOCKER) should have caught these before publish
- If you skipped validation, run `/ba-amend` manually against the current files and resolve all TBC flags before re-publishing

**`uv run msc-mcp-server` fails with dependency errors**
- Run `uv sync` from the `mcp/` directory to reinstall dependencies
- Confirm Python 3.12+ is active: `python3 --version`

**Stories contain an ADF interface (Rule 4 BLOCKER)**
- The ADF interface was not caught during story generation
- Run `/ba-amend`, find the Rule 4 flag, and choose "Accept fix" to remove the ADF story

**Weekly metrics report not appearing**
- The scheduled task runs while Codemie is open — if the app is closed at 5pm Friday it runs on next launch
- Generate the report manually at any time with `/ba-metrics-report`

---

## 14. Glossary

| Term | Meaning |
|---|---|
| **BA** | Business Analyst |
| **SA** | Solution Architect |
| **CR** | Change Request — a story type for changes to existing interfaces |
| **US** | User Story — a story type for new interfaces |
| **ADF** | A category of MSC interface (e.g. ADF108, ADF204) owned by a separate team — always excluded from BA stories |
| **INT** | Interface identifier prefix (e.g. INT710v2, INT025) |
| **DTTP** | Digital Transformation Programme — the MSC programme this team supports |
| **EINT** | Enterprise Integration — the EPAM team delivering MuleSoft integration work |
| **MCP** | Model Context Protocol — the local server that gives Codemie access to Jira and Confluence tools |
| **TBC** | To Be Confirmed — a placeholder inserted when the agent cannot find a value in the source materials |
| **Codemie** | EPAM's internal deployment of Claude. Always use `codemie-claude`, never `claude` |
| **BLOCKER** | Validation severity: must be resolved before publishing |
| **WARNING** | Validation severity: recommended fix; publishing is allowed but quality is reduced |
| **INFO** | Validation severity: optional improvement |
| **Feedback loop** | One complete amend + re-validate cycle; tracked in metrics |
| **Structural rules** | Validation Rules 9–14: enforce template structure (sections present, table columns correct, summary length, BDD format). Run before content rules. |
| **Content quality rules** | Validation Rules 1–8: enforce completeness and traceability (TBC fields, vague ACs, ADF slippage, CR/US splits). Run after structural rules. |
| **Intake** | Optional Phase 0 — preprocesses PDFs, meeting recordings, Confluence pages into clean Markdown before spec generation |
| **distill-doc** | Installed skill used by the intake phase to extract text from PDF files (classical parsing + AI vision) |
| **enrich-meeting** | Installed skill used by the intake phase to enrich VTT transcripts with video frame descriptions |
| **Template auto-fix** | When a pre-save validator finds violations, the generating agent automatically regenerates the offending section and re-validates once. Counted in metrics. |
| **Validation mode** | The review method chosen after each generation phase: Conversational / Automated / Both / Skip |
| **AEM** | Adobe Experience Manager — the CMS replacing Sitecore |
| **CDP** | Adobe Customer Data Platform |
| **AJO** | Adobe Journey Optimizer |
| **DTS** | MSC's core reservation system |
| **CHUB** | Customer Hub — MSC's internal CRM data service |
| **Datatrans** | Payment gateway used in the booking flow |
| **Atlassian API token** | A personal access token from `id.atlassian.com` used to authenticate with Jira and Confluence |
| **uv** | A fast Python package manager used to install and run the MCP server |
| **Draft (Confluence)** | A saved but unpublished version of a Confluence page — all agent updates are saved this way |
| **`output/metrics/`** | Directory containing per-feature JSON metrics files and weekly report subdirectory |
| **`mcp/.env`** | Local config file holding your credentials — never committed to Git |
