# MSC Mule BA Agent

AI-assisted BA toolkit for the MSC Cruises MuleSoft Integration team (DTTP programme).

It takes raw input materials — pasted text, existing documents, or Confluence pages — and produces a functional specification, Jira-ready BA stories, a validation report, and publishes the outputs to Jira and Confluence.

---

## How to invoke

> **`codemie-claude`** is EPAM's internal wrapper around Claude Code. It handles authentication against the Codemie platform and is required for use within EPAM-managed environments. See `docs/SETUP.md` for installation instructions. If you are running standard Claude Code directly (e.g. outside EPAM infrastructure), replace `codemie-claude` with `claude` in all commands below.

Open a terminal, navigate to the project, and run:

```bash
codemie-claude -p "/ba-workflow"
```

This starts the main orchestrator, which will guide you through the full pipeline interactively.

To invoke a specific agent or skill directly:

```bash
# Generate a spec from input materials
codemie-claude -p "/ba-workflow" --input "generate spec for <feature name>"

# Run the full pipeline non-interactively (end-to-end)
codemie-claude -p "Run the ba-workflow end-to-end for <feature name> using <input file or text>"
```

**Standard Claude Code fallback:**
```bash
claude -p "/ba-workflow"
```

---

## Pipeline overview

```
Input materials
      │
      ▼
┌─────────────────────────┐
│  functional-spec-        │  Produces output/specs/functional_spec_<req-id>_[name].html
│  generator (agent)       │  Sections: Reference Docs, Feature Summary,
│                          │  Business Requirements, Use Cases, NFRs,
│                          │  Test Scenarios & Acceptance Criteria
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  ba-story-generator      │  Produces output/stories/[name].md
│  (agent)                 │  Generates CRs and User Stories
│                          │  Applies ADF exclusion and splitting rules
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  ba-validator (agent)    │  Produces output/validation/validation-report.md
│                          │  Flags: TBC fields, vague ACs, missing links,
│                          │  ADF slippage, wrong CR/US splits, missing owners
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  ba-amend (skill)        │  Interactive: Accept / Edit manually / Skip
│                          │  Applies fixes directly to specs and stories files
└──────────┬──────────────┘
           │
      ┌────┴────┐
      ▼         ▼
┌──────────┐  ┌───────────────────┐
│  jira-   │  │  confluence-      │
│ publisher│  │  publisher        │
│ (agent)  │  │  (agent)          │
│          │  │                   │
│ Updates  │  │ Updates page      │
│ existing │  │ BA sections only  │
│ tickets  │  │ Saves as DRAFT    │
└──────────┘  └───────────────────┘
```

---

## Agents and skills

| File | Type | Invoked by |
|------|------|------------|
| `agents/functional-spec-generator.md` | Agent | `ba-workflow`, or directly |
| `agents/ba-story-generator.md` | Agent | `ba-workflow`, or directly |
| `agents/ba-validator.md` | Agent | `ba-workflow`, or directly |
| `agents/jira-publisher.md` | Agent | `ba-workflow`, or directly |
| `agents/confluence-publisher.md` | Agent | `ba-workflow`, or directly |
| `.claude/commands/ba-amend.md` | Skill | `/ba-amend`, or via `ba-workflow` |
| `.claude/commands/ba-workflow.md` | Skill | `/ba-workflow` |

---

## Output folder structure

```
output/
├── specs/
│   └── functional_spec_[feature_name].html   ← generated functional specification
│
├── stories/
│   ├── [initiative-slug]-cr-001.md            ← one file per CR
│   └── [initiative-slug]-us-001.md            ← one file per User Story
│
└── validation/
    └── validation-report.md                  ← flags, severities, and suggested fixes
```

---

## MCP server (Jira & Confluence integration)

The Jira and Confluence tools require the local MCP server to be running. Start it in a second terminal before using any publish agents:

```bash
cd "C:\Users\[your_user]\MSC- Mule BA Agent\mcp"
uv run msc-mcp-server
```

Credentials are configured in `mcp/.env` — see `docs/SETUP.md` for setup instructions.

---

## Key rules the agents follow

- **Never invent content** — missing information is always marked `[TO BE CONFIRMED]`
- **ADF interfaces are always excluded** from story generation
- **New interfaces** always get individual User Stories, never CRs
- **Confluence pages are always saved as draft** — a human must publish manually
- **Protected Confluence sections** (Solution Overview, Involved Interfaces, Sequence Diagrams, Monitoring and Alerting Guidelines) are never overwritten by the BA agents
- **Jira publisher never creates or deletes tickets** and never transitions status
