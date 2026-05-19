# MSC Mule BA Agent — User Guide

An AI assistant for Business Analysts on the MSC Cruises MuleSoft Integration team. It takes your raw input materials and produces a functional specification, Jira-ready BA stories, and publishes them to Jira and Confluence.

---

## First-time setup

Follow `docs/SETUP.md` once before using the agent for the first time. It covers installing Claude Code, configuring your Atlassian API credentials, and starting the MCP server.

---

## Every session — start here

You need **two terminals** open each time you work.

**Terminal 1 — MCP server** (keep this running in the background):
```bash
cd "C:\Users\[your_user]\MSC_BA_Agent\MSC_BA_Agent\mcp"
uv run msc-mcp-server
```

> **Windows note:** If `uv` is not found, use the full path:
> ```bash
> /c/Users/[your_user]/AppData/Roaming/Python/Python314/Scripts/uv.exe run msc-mcp-server
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
2. Stories only         — generate Jira BA stories from an existing spec
3. Full end-to-end      — spec → stories → validate → amend → publish
4. Validate and publish — validate existing output and publish to Jira / Confluence
```

Choose the option that matches what you need. Claude will guide you through each step interactively.

---

## What to provide as input materials

When prompted for input materials, you can provide any combination of:

- **Pasted text** — copy and paste an email, Teams message, meeting notes, or requirements description directly into the chat
- **File paths** — e.g. `C:\Users\[your_user]\Documents\requirements.docx`
- **Confluence page URLs** — e.g. `https://msccruises.atlassian.net/wiki/spaces/...` — the agent will fetch the page content live via the MCP server
- **Jira ticket URLs** — e.g. `https://smartship.atlassian.net/browse/MDTTPU-1234`
- **Sequence diagrams** — paste PlantUML directly into the chat
- **Images** — describe what an image shows or share a file path

The more detail you provide, the fewer `[TO BE CONFIRMED]` gaps will appear in the output.

---

## What gets produced

| Output | Location | Description |
|--------|----------|-------------|
| Functional specification | `output/specs/functional_spec_[name].html` | HTML spec ready for Confluence |
| BA stories | `output/stories/[name].html` | Change Requests and User Stories ready for Jira |
| Validation report | `output/validation/validation-report.md` | Flags issues before publishing |

---

## Publishing to Jira and Confluence

### Jira
When publishing to Jira, provide the ticket key(s) you want to update (e.g. `MDTTPU-8133`). The agent updates the description and acceptance criteria only — it never creates, deletes, or transitions tickets.

### Confluence
When publishing to Confluence, provide the page URL. The agent:

- Updates all **BA-owned sections** from the spec (Reference Documentation, Feature Summary, Business Requirements, Use Cases, Non-Functional Requirements, Test Scenarios & Acceptance Criteria)
- **Preserves SA-owned sections** verbatim (Solution Overview, Involved Interfaces, Sequence Diagrams, Monitoring and Alerting Guidelines)
- **Preserves all Confluence macros** (`ac:` and `ri:` tags) exactly as they appear on the page — including TOC macros, PlantUML diagrams, whiteboard embeds, and status macros
- **Appends a new Document History row** with the date using the Confluence date macro — never edits existing rows
- **Hyperlinks all URLs** — no plain text URLs are written to the page
- **Always saves as a draft** — you must review and publish manually in Confluence

The draft URL format is: `https://msccruises.atlassian.net/pages/resumedraft.action?draftId=[page_id]`

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
│   └── [feature_name].html                   ← Jira-ready CRs and User Stories
│
└── validation/
    └── validation-report.md                  ← flags, severities, and suggested fixes
```

---

## Reference documents

| Document | Location | Description |
|---|---|---|
| Setup guide | `docs/SETUP.md` | First-time environment setup |
| Confluence publisher instructions | `docs/confluence-publisher-agent-instructions.html` | Full list of BA and SA publisher agent rules, section ownership, and draft API details |
| MCP server guide | `mcp/README_MCP.md` | MCP server setup and tool reference |
| MSC context | `knowledge/MSC_CONTEXT.md` | Programme background, system glossary, rollout timeline |

---

## Key things to know

- **Missing information is never invented** — gaps are always marked `[TO BE CONFIRMED]` for you to fill in later
- **ADF interfaces are excluded** from story generation (e.g. ADF108) — this is by design, they are owned by another team
- **Confluence pages are always saved as drafts** — a human must review and publish manually
- **SA-owned sections are never touched** — Solution Overview, Involved Interfaces, Sequence Diagrams, and Monitoring & Alerting Guidelines are preserved exactly as the Solution Architect left them
- **All Confluence macros are preserved** — TOC, PlantUML, whiteboard embeds, and any other `ac:` macros are copied verbatim from the current page
- **Jira tickets are never created or deleted** — the agent only updates existing tickets you point it to
- **Confluence page fetching** — the agent reads live Confluence pages via the MCP server when you provide a URL as input material; the MCP server must be running for this to work

---

## Troubleshooting

**MCP server not starting — "uv: command not found"**
Use the full path to uv on Windows:
```bash
/c/Users/[your_user]/AppData/Roaming/Python/Python314/Scripts/uv.exe run msc-mcp-server
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
Your API token may have expired. Generate a new one at https://id.atlassian.com/manage/api-tokens and update `mcp/.env`. See `docs/SETUP.md` for details.

**Confluence draft is empty after publishing**
This happens when the HTML body is not correctly escaped in the API call. The agent uses Python `json.dump()` to avoid this — if it recurs, re-run the publish step.

**Output files look wrong or incomplete**
Run option **4 — Validate and publish** to get a validation report. It will flag exactly what needs to be fixed before publishing.
