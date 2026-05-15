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
cd "C:\Users\[your_user]\MSC- Mule BA Agent\mcp"
uv run msc-mcp-server
```

You should see:
```
MSC BA MCP Server running on http://localhost:8080
```

**Terminal 2 — Claude Code** (this is where you work):
```bash
cd "C:\Users\[your_user]\MSC- Mule BA Agent"
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
- **Confluence page URLs** — e.g. `https://msccruises.atlassian.net/wiki/spaces/...`

The more detail you provide, the fewer `[TO BE CONFIRMED]` gaps will appear in the output.

---

## What gets produced

| Output | Location | Description |
|--------|----------|-------------|
| Functional specification | `output/specs/functional_spec_[name].html` | HTML spec ready for Confluence |
| BA stories | `output/stories/[name].md` | Change Requests and User Stories ready for Jira |
| Validation report | `output/validation/validation-report.md` | Flags issues before publishing |

---

## Publishing to Jira and Confluence

When you reach the publish step, Claude will ask for:

- **Jira**: the ticket key(s) you want to update (e.g. `DTTP-123`). Claude updates the description and acceptance criteria only — it never creates, deletes, or transitions tickets.
- **Confluence**: the page URL you want to update. Claude updates the BA-owned sections only and always saves as a **draft** — you must review and publish manually in Confluence.

---

## Key things to know

- **Missing information is never invented** — gaps are always marked `[TO BE CONFIRMED]` for you to fill in later.
- **ADF interfaces are excluded** from story generation (e.g. ADF108). This is by design.
- **Confluence pages are always saved as drafts** — a human must review and publish.
- **SA-owned sections are never touched** — Solution Overview, Involved Interfaces, Sequence Diagrams, and Monitoring & Alerting Guidelines are preserved exactly as the Solution Architect left them.
- **Jira tickets are never created or deleted** — the agent only updates existing tickets you point it to.

---

## Troubleshooting

**"MCP server not connected"**
Check that Terminal 1 is still running. If it stopped, restart it with `uv run msc-mcp-server`.

**Claude is not responding to `/ba-workflow`**
Make sure you are in the project directory when you launch Claude Code:
```bash
cd "C:\Users\[your_user]\MSC- Mule BA Agent"
codemie-claude
```

**Confluence or Jira errors (401 / 403)**
Your API token may have expired. Generate a new one at https://id.atlassian.com/manage/api-tokens and update `mcp/.env`. See `docs/SETUP.md` for details.

**Output files look wrong or incomplete**
Run option **4 — Validate and publish** to get a validation report. It will flag exactly what needs to be fixed before publishing.
