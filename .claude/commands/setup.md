# /setup — First-Time Environment Setup

Walk the designer through a complete environment setup from scratch.

## What this command does
1. Checks prerequisites (Python, uv)
2. Collects all credentials interactively
3. Writes `mcp/.env` file
4. Starts the MCP server
5. Configures Claude Code MCP settings
6. Verifies everything works

---

## Steps

### Step 1: Check prerequisites

Run these checks and report status:
```bash
python --version        # Need 3.10+
uv --version            # Need uv package manager
```

If Python missing: "Install Python 3.10+ from python.org"
If uv missing: "Run: pip install uv  OR  curl -LsSf https://astral.sh/uv/install.sh | sh"

### Step 2: Check if .env exists

```bash
test -f mcp/.env && echo "EXISTS" || echo "NOT FOUND"
```

If exists, ask: "An .env file already exists. Re-configure? (yes/no)"
If no or re-configure:

### Step 3: Collect credentials

Ask these questions ONE BY ONE (not all at once):

**Confluence (Production)**
- "What is your Confluence URL? (e.g. https://msccruises.atlassian.net)"
- "What is your Confluence email?"
- "What is your Confluence API token? (get it at: https://id.atlassian.com/manage/api-tokens)"

**Confluence (Sandbox) — optional but recommended**
Say: "Do you have access to a Confluence sandbox space? Sandbox lets you publish draft pages for review before going live.
⚠️ If you don't have sandbox access, that's fine — local previews will always be available and are fully usable for review. Sandbox is just an optional extra step."
- "Do you have a sandbox Confluence instance? (yes/no)"
- If yes: "Is it on a different URL from production? (yes/no)"
  - If different: collect separate sandbox URL, email, token
  - If same: "Got it, I'll use the same credentials for sandbox"
- If no: "No problem. All generated pages will be saved locally to `previews/` and rendered in your browser. You can always add sandbox credentials later by running /setup again."

**Jira (optional)**
- "Do you use Jira integration? (yes/no — needed for /jira command)"
- If yes:
  - "Jira URL? (usually same as Confluence, e.g. https://msccruises.atlassian.net)"
  - "Jira email? (usually same as Confluence)"
  - "Jira API token? (usually same token)"

**MCP Server**
- "Which port for the MCP server? (default: 8080, press Enter to keep)"

### Step 4: Write .env file

Write to `mcp/.env`:
```
MSC_CONFLUENCE_URL={confluence_url}
MSC_CONFLUENCE_EMAIL={email}
MSC_CONFLUENCE_TOKEN={token}
MSC_CONFLUENCE_SANDBOX_URL={sandbox_url}
MSC_CONFLUENCE_SANDBOX_EMAIL={sandbox_email}
MSC_CONFLUENCE_SANDBOX_TOKEN={sandbox_token}
MSC_JIRA_URL={jira_url}
MSC_JIRA_EMAIL={jira_email}
MSC_JIRA_TOKEN={jira_token}
MSC_PORT={port}
MSC_TRANSPORT=streamable-http
```

Confirm: "✅ Credentials saved to mcp/.env"

### Step 5: Install dependencies

```bash
cd mcp && uv sync
```

Report: "✅ Dependencies installed"

### Step 6: Show MCP server start instructions

Tell the designer:
"Start the MCP server in a SEPARATE terminal:
```bash
cd mcp
uv run msc-mcp-server
```
Keep that terminal open. The server must be running for Claude to use Confluence/Jira tools.

Type **'ready'** when the server is running and you see the startup message."

Wait for the designer to type 'ready' (or any confirmation) before continuing.

### Step 7: Register MCP server in Claude Code

Run this command to register the MCP server automatically:
```bash
claude mcp add msc --transport http http://localhost:{port}/mcp
```

If the command succeeds, report: "✅ MCP server registered"
If it fails (e.g. `claude` not in PATH), tell the designer:
"Automatic registration failed. Add it manually in Claude Code: Settings → MCP Servers → Add:
```json
{ "mcpServers": { "msc": { "url": "http://localhost:{port}/mcp" } } }
```
Type **'done'** when added."

### Step 8: Prompt restart and end wizard

Tell the designer:

```
✅ Setup saved!

One last step: restart Claude Code so the MCP server connection takes effect.

How to restart Claude Code:
  • Desktop app: press Ctrl+R (Windows/Linux) or Cmd+R (Mac)
    — or close and reopen the app
  • VS Code extension: open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
    → type "Claude: Restart" and select it
    — or close and reopen the VS Code window
  • CLI (terminal): type /exit to quit, then run `claude` again in this folder

After restart:
  1. Keep the MCP server terminal running — do not close it
  2. Open Claude Code in this folder again
  3. Type: /setup verify

That will confirm Confluence and Jira are connected and you're ready to work.
```

Stop here. Do not attempt to call any MCP tools — they will not be available until after restart.

---

## Verify Mode

**Triggered when the designer runs `/setup verify` after restarting Claude Code.**

### Verify Step 1: Check MCP connection

Call `hello_world` tool.
- If it responds: "✅ MCP server connected!"
- If it fails: "❌ MCP server not reachable. Is the server running? Check the terminal where you ran `uv run msc-mcp-server`. If it stopped, restart it and try again."

Call `health_check` tool — show the response.
Call `server_info` tool — show which integrations are active.

### Verify Step 2: Test Confluence access

Ask: "Let's confirm Confluence works. Do you have a Confluence page ID to test with? (any page ID — or type 'skip')"

If provided: call `confluence_get_markdown(page_id)` — show first 3 lines and confirm: "✅ Confluence connected!"
If skipped: note it as unverified.

### Verify Step 3: Show ready summary

```
🎉 MSC API Designer is ready!

✅ MCP server connected (port {port})
✅ Confluence connected ({url})
{✅ Sandbox configured / ℹ️  No sandbox — local previews available in previews/}
{✅/⚠️} Jira {connected/not configured}

Quick start:
  /generate   — generate full page set for a new endpoint
  /validate   — check consistency across all pages
  /explain    — ask any question about MSC API conventions
  /status     — check design progress for an interface

Reference pages (INT004.4 Klarna):
  MUL:  4325507083  |  EAPI: 4072473378
  PAPI: 4476535093  |  SAPI: 4156620801
```
