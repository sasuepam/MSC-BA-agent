# Setup Guide — MSC Mule BA Agent

Everything you need to go from zero to working in under 10 minutes.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Claude Code | Latest | https://claude.ai/code |
| Python | 3.12+ | https://python.org |
| uv | Latest | `pip install uv` |
| Atlassian API token | — | https://id.atlassian.com/manage/api-tokens |

---

## Step 1 — Open Claude Code

```bash
cd "MSC- Mule BA Agent"
claude
```

Claude Code opens in your terminal. Claude immediately knows all MSC BA conventions from `CLAUDE.md` — no extra configuration needed.

---

## Step 2 — Configure credentials

Copy the example env file and fill in your values:

```bash
cd mcp
cp .env.example .env
```

Edit `mcp/.env` and fill in:

```
MSC_JIRA_URL=https://msccruises.atlassian.net
MSC_JIRA_EMAIL=your.email@msccruises.com
MSC_JIRA_TOKEN=your-api-token

MSC_CONFLUENCE_URL=https://msccruises.atlassian.net
MSC_CONFLUENCE_EMAIL=your.email@msccruises.com
MSC_CONFLUENCE_TOKEN=your-api-token
```

Generate an API token at: https://id.atlassian.com/manage/api-tokens

---

## Step 3 — Install dependencies

```bash
cd mcp
uv sync
```

---

## Step 4 — Start the MCP server

Open a **second terminal** and keep it running throughout your session:

```bash
cd "MSC- Mule BA Agent/mcp"
uv run msc-mcp-server
```

You should see:
```
MSC BA MCP Server running on http://localhost:8080
```

**Keep this terminal open.** The server must be running for Claude to access Confluence and Jira.

---

## Step 5 — Configure Claude Code MCP

Run once in any terminal:

```bash
claude mcp add msc-ba --transport http http://localhost:8080/mcp
```

Or manually add to Claude Code settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "msc-ba": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

---

## Step 6 — Verify everything works

Back in Claude Code, test it:

```
hello, can you check if the MCP server is connected?
```

Claude should call `hello_world()` and return a confirmation message. If it does — you're ready.

---

## Daily workflow

Every day you work:
1. Open terminal → `cd "MSC- Mule BA Agent" && claude`
2. Open second terminal → `cd mcp && uv run msc-mcp-server`
3. Work in Claude Code

The MCP server needs to be restarted each session.

---

## Available agents

| Say... | Agent activates |
|--------|----------------|
| "generate functional spec for..." | `functional-spec-generator` |
| "create user stories for..." | `ba-story-generator` |
| "read Confluence page..." | `confluence_get_markdown` tool |
| "search Jira for..." | `jira_search` tool |
| "create a Jira ticket for..." | `jira_create_issue` tool |

---

## Troubleshooting

### "MCP server not connected"
- Is the MCP server running? Check the second terminal.
- Did you add the MCP config to Claude Code? Run `claude mcp list` to check.
- Is port 8080 free? If not, change `MSC_PORT` in `mcp/.env` and update the MCP URL.

### "Confluence 401 Unauthorized"
- Check `MSC_CONFLUENCE_TOKEN` in `mcp/.env` — API tokens expire and must be regenerated.
- Check `MSC_CONFLUENCE_EMAIL` matches the account that owns the token.

### "uv: command not found"
```bash
pip install uv
# or on Mac/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Python version too old"
The MCP server requires Python 3.12+. Check: `python --version` or `python3 --version`.
