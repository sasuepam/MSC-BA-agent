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
   - [Phase: Spec](#71-phase-spec)
   - [Phase: Stories](#72-phase-stories)
   - [Phase: Validate](#73-phase-validate)
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

The BA Agent is an AI-assisted toolkit that turns raw input — emails, meeting notes, Confluence pages, Jira tickets, sequence diagrams — into structured BA documentation ready for development.

It runs entirely inside **Codemie**, EPAM's internal deployment of Claude. This matters for two reasons:

- All client data stays inside EPAM's tenant. **Never use the public `claude` or `claude-code` CLI with MSC data.**
- The agent has access to MSC's Jira and Confluence through a local MCP server you run on your machine.

The agent is opinionated about the MSC MuleSoft integration context. It knows the DTTP programme, the ADF exclusion rule, the 11-section functional spec format, and the exact CR/US splitting rules. You feed it raw material; it applies those rules and produces artefacts.

---

## 2. What It Does and Doesn't Do

### It does

| Capability | Detail |
|---|---|
| Generate functional specs | 11-section HTML spec from any combination of input materials |
| Generate Change Requests | One CR per logical change across one or many existing interfaces |
| Generate User Stories | One US per new interface introduced |
| Validate artefacts | 8 rules across spec and story files; BLOCKER / WARNING / INFO severities |
| Amend artefacts interactively | Walk through every validation flag; apply, edit, or skip each one |
| Publish to Jira | Update description and acceptance criteria on existing tickets only |
| Publish to Confluence | Update BA sections of a spec page, always saving as draft |
| Track metrics | Time per phase, iteration counts, token usage, cost per feature |

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
(email / notes / Confluence URL / Jira URL / diagram / image)
        │
        ▼
  [PHASE: SPEC]  ──► output/specs/functional_spec_[feature].html
        │
        ▼
[PHASE: STORIES] ──► output/stories/[feature].html
        │
        ▼
[PHASE: VALIDATE] ──► output/validation/validation-report.md
        │
   BLOCKERs? ──Yes──► [PHASE: AMEND] ──► re-validate
        │ No
        ▼
[PHASE: PUBLISH] ──► Jira ticket descriptions + Confluence draft page
        │
        ▼
   output/metrics/metrics_[feature].json
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
2. Generate stories from existing spec
3. Full end-to-end (spec → stories → validate → amend → publish)
4. Validate and publish existing artefacts
```

**Choice 3** is the most common for a new feature. **Choice 4** is for returning to work you started in a previous session.

---

### 7.1 Phase: Spec

The spec phase invokes the `functional-spec-generator` agent. You provide your input materials at the prompt.

**What it produces:** `output/specs/functional_spec_[feature_name].html`

The spec has 11 sections. The agent fills the BA-owned sections (1–5, 9, 11) from your materials and leaves the SA-owned sections (6–8, 10) blank for the Solution Architect to complete later.

**What to provide as input:**

- Paste raw text directly into the prompt (email content, meeting notes, requirements)
- Give a file path: `docs/my_requirements.txt`
- Give a Confluence URL: the agent will read the page
- Give a Jira URL: the agent will read the ticket description
- Give multiple at once — the agent correlates across all sources

**What you get back:**

- The saved file path
- A list of all `[TO BE CONFIRMED]` fields — gaps where you'll need to fill in real values
- A count of gaps

**Tip:** More input is always better. Paste the full email thread, not just the summary. The agent never makes things up; it can only work with what you give it.

---

### 7.2 Phase: Stories

The stories phase invokes the `ba-story-generator` agent. It reads the spec you just created.

**What it produces:** `output/stories/[feature_name].html`

**CR vs US — the splitting rule:**

| Situation | Output |
|---|---|
| Existing interface being changed | Change Request (CR) |
| New interface being introduced | User Story (US) — one per interface |
| Same change across multiple existing interfaces | One CR covering all |
| Multiple different changes under the same feature | Separate CRs per change type |
| ADF-prefixed interface | Excluded — not produced at all |

**What you get back:**

- The saved file path
- CR count and US count
- A list of any ADF interfaces that were excluded
- Any remaining gaps

---

### 7.3 Phase: Validate

The validation phase invokes the `ba-validator` agent across all files in `output/specs/` and `output/stories/`.

**What it produces:** `output/validation/validation-report.md`

**The 8 rules:**

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

**BLOCKERs must be resolved before publishing.** WARNINGs are recommended fixes. INFOs are quality improvements.

---

### 7.4 Phase: Amend

When BLOCKERs are found, the workflow automatically moves to the amend phase. You can also run it manually with `/ba-amend`.

The agent reads the validation report and walks you through every flag in severity order (BLOCKERs first).

For each flag, you choose:

- **Accept fix** — Claude applies the suggested edit directly to the file
- **Edit manually** — you provide the replacement text, Claude applies it
- **Skip** — flag stays unresolved (you'll be warned before publishing if it's a BLOCKER)

After all flags are handled, you get an Amendment Summary showing Applied / Edited / Skipped counts and which files were modified.

---

### 7.5 Phase: Publish

After validation passes (zero BLOCKERs), you choose where to publish:

**Option A — Jira only:** Provide one or more ticket keys (e.g. `DTTP25-1234`). The agent reads the matching story from `output/stories/`, shows you a preview of the description and acceptance criteria, asks for confirmation, then updates the ticket.

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
| `/ba-amend` | Interactive flag resolution | Manually re-run amendments, or when called by `/ba-workflow` |
| `/ba-metrics` | Summary table of all tracked features | Review your output at any time |
| `/ba-metrics --detail [slug]` | Per-phase breakdown for one feature | Deep dive on a single feature |
| `/setup` | First-time setup wizard | First install only, or to update credentials |
| `/setup verify` | Ping MCP server and check all integrations | After install, or when troubleshooting connectivity |

---

## 9. Understanding the Outputs

```
output/
├── specs/
│   └── functional_spec_[feature_name].html      ← 11-section spec, plain HTML
│
├── stories/
│   └── [feature_name].html                      ← CRs and User Stories, plain HTML
│
├── validation/
│   └── validation-report.md                     ← Flag list with severities
│
└── metrics/
    └── metrics_[feature_slug].json              ← Timing, tokens, cost
```

**Spec files** are plain HTML with no embedded CSS. They're designed to paste cleanly into Confluence. Tables use `border="1" cellpadding="5" cellspacing="0"` and nothing else.

**Story files** follow the CR and US templates in `knowledge/templates/`. Each CR and US is a self-contained HTML block.

**Validation reports** are Markdown. Each flag is a block with: FLAG-NNN, rule number, severity, file, section, description of the issue, and a suggested fix.

**Metrics files** are JSON. Use `/ba-metrics` to read them — you don't need to open the JSON directly.

---

## 10. Metrics — Tracking Your Work

Every feature run automatically creates `output/metrics/metrics_[slug].json`. This file tracks:

- Session start and end timestamps
- Total session duration in minutes
- Per-phase timestamps, durations, and iteration counts
- Validation run history (blocker/warning/info counts per run)
- Amend run history (applied/edited/skipped per run)
- Feedback loop count (incremented each time you amend and re-validate)
- Jira tickets updated and Confluence page URL
- Token usage (input, output, total) and estimated cost in USD

**To see a summary across all features:**

```
/ba-metrics
```

Output: a table with slug, status, total time, feedback loops, tokens, cost.

**To see per-phase detail for one feature:**

```
/ba-metrics --detail free_balcony_upgrade
```

Output: started/completed timestamps per phase, duration, CR/US counts, every validation and amend run, publish targets.

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
Generate the story for INT[number] only and add it to the existing stories file.
```

---

### Validation phase prompts

**Running validation manually:**
```
Run validation on the current spec and stories files.
```

**Checking only for BLOCKERs:**
```
Run validation and report only the BLOCKER flags. I'll handle WARNINGs and INFOs later.
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

**Detailed view of one feature:**
```
/ba-metrics --detail [feature_slug]
```

**Listing features with unresolved TBCs:**
```
/ba-metrics

Which of these features still have status "in_progress"?
```

---

## 12. Tips and Best Practices

**Give the agent everything, not just the summary.** The agent can only work from what you provide. A full email thread is better than a paraphrase. A Confluence page URL is better than a description of what's on the page.

**Resolve TBCs before generating stories.** Stories inherit TBC fields from the spec, which will then become BLOCKERs in validation. It's faster to fill in TBCs in the spec first.

**Use the sandbox Confluence instance for experiments.** Your `mcp/.env` can have a separate sandbox URL. When the agent asks which instance to publish to, choose sandbox until you're confident in the output.

**Re-validate after every amendment session.** The amend phase can resolve some flags while introducing edge cases. A quick re-validation confirms you're clean.

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

**[TO BE CONFIRMED] fields are still in the published output**
- Validation Rule 1 (BLOCKER) should have caught these before publish
- If you skipped validation, run `/ba-amend` manually against the current files and resolve all TBC flags before re-publishing

**`uv run msc-mcp-server` fails with dependency errors**
- Run `uv sync` from the `mcp/` directory to reinstall dependencies
- Confirm Python 3.12+ is active: `python3 --version`

**Stories contain an ADF interface (Rule 4 BLOCKER)**
- The ADF interface was not caught during story generation
- Run `/ba-amend`, find FLAG-xxx (Rule 4), and choose "Accept fix" to remove the ADF story

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
| **AEM** | Adobe Experience Manager — the CMS replacing Sitecore |
| **CDP** | Adobe Customer Data Platform |
| **AJO** | Adobe Journey Optimizer |
| **DTS** | MSC's core reservation system |
| **CHUB** | Customer Hub — MSC's internal CRM data service |
| **Datatrans** | Payment gateway used in the booking flow |
| **Atlassian API token** | A personal access token from `id.atlassian.com` used to authenticate with Jira and Confluence |
| **uv** | A fast Python package manager used to install and run the MCP server |
| **Draft (Confluence)** | A saved but unpublished version of a Confluence page — all agent updates are saved this way |
| **`output/metrics/`** | Directory containing per-feature JSON metrics files |
| **`mcp/.env`** | Local config file holding your credentials — never committed to Git |
