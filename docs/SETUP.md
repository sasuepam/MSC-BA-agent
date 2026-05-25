# Setup Guide — MSC Mule BA Agent

A complete walkthrough for getting the MSC Mule BA Agent running on a new machine, from cloning the repository to running your first workflow.

**Estimated time:** 15–20 minutes

> ⚠️ **Important — use `codemie-claude`, not `claude`**
> This project runs on **Codemie**, EPAM's private, client-safe deployment of Claude Code. Always use the `codemie-claude` command to launch it. Do **not** use the standard `claude` CLI — that routes to Anthropic's public service and must not be used with client data. Every command in this guide uses `codemie-claude`.

---

## Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the repository](#2-clone-the-repository)
3. [Launch Claude Code](#3-launch-claude-code)
4. [Run /setup — interactive configuration wizard](#4-run-setup--interactive-configuration-wizard)
5. [Start the MCP server](#5-start-the-mcp-server)
6. [Restart Claude Code and verify](#6-restart-claude-code-and-verify)
7. [Your daily workflow](#7-your-daily-workflow)
8. [Manual configuration reference](#8-manual-configuration-reference)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

Install the following before you begin. All four are required.

### Git
Used to clone the repository.
- **Windows:** Download from https://git-scm.com/download/win and run the installer
- **Mac:** Run `git --version` in Terminal — if not installed, macOS will prompt you to install it
- **Verify:** `git --version`

### Python 3.12 or later
Required by the MCP server. Earlier versions will not work.
- Download from https://www.python.org/downloads/
- **Windows:** During installation, tick **"Add Python to PATH"**
- **Verify:** `python --version` (Windows) or `python3 --version` (Mac/Linux)

### uv
A fast Python package manager used to install and run the MCP server.
```bash
pip install uv
```
- **Mac/Linux alternative:**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Verify:** `uv --version`

### Codemie (Claude Code)
The AI coding assistant that runs the BA agents. This project uses **Codemie** — EPAM's private, client-safe deployment of Claude Code. Do not use the standard `claude` CLI.
- Install Codemie by following your team's internal Codemie onboarding instructions
- **Verify:** `codemie-claude --version`

### Atlassian API token
Required to connect to Jira and Confluence. You will need it during the `/setup` wizard in Step 4.
- Go to https://id.atlassian.com/manage/api-tokens
- Click **Create API token**, give it a label (e.g. `MSC BA Agent`), and copy the token
- One token covers both Jira and Confluence — keep it somewhere safe, you cannot view it again after closing the page

---

## 2. Clone the repository

Open a terminal and clone the repository:

```bash
git clone https://github.com/sasuepam/MSC-BA-agent.git
```

This creates a folder called `MSC-BA-agent`. Navigate into it:

```bash
cd MSC-BA-agent
```

> **Windows — choosing a location:**
> ```bash
> cd "C:\Users\[your_user]\Documents"
> git clone https://github.com/sasuepam/MSC-BA-agent.git
> cd MSC-BA-agent
> ```

Your project root should contain:
```
MSC-BA-agent/
├── agents/
├── .claude/
│   └── commands/
│       ├── ba-workflow.md
│       ├── ba-amend.md
│       └── setup.md          ← the /setup wizard lives here
├── docs/
├── knowledge/
├── mcp/
├── output/
├── CLAUDE.md
└── README.md
```

---

## 3. Launch Claude Code

Open Codemie **from the project root** — this is important. The agents, skills, and `CLAUDE.md` conventions only load when Codemie is started from this folder.

```bash
cd "C:\Users\[your_user]\Documents\MSC-BA-agent"
codemie-claude
```

> **Mac/Linux:**
> ```bash
> cd ~/Documents/MSC-BA-agent
> codemie-claude
> ```

Codemie opens in your terminal. You are now ready to run the setup wizard.

---

## 4. Run /setup — interactive configuration wizard

The `/setup` command is a built-in wizard that guides you through the entire configuration in one go. Once Claude Code is open, type:

```
/setup
```

The wizard will walk you through the following steps automatically:

### What /setup does

**Step 1 — Checks prerequisites**
Verifies that Python and uv are installed and accessible. Reports the version found or tells you exactly what to install if something is missing.

**Step 2 — Checks for an existing .env file**
If a `mcp/.env` already exists, it asks whether you want to re-configure. Useful if you need to update a token or add a new integration.

**Step 3 — Collects your credentials interactively, one question at a time**

It asks for:
- Confluence URL (e.g. `https://msccruises.atlassian.net`)
- Confluence email address
- Confluence API token (paste the one you generated in Step 1)
- Whether you have a Confluence sandbox space (optional — used for draft review before going live)
- Whether you use Jira integration, and if so your Jira URL, email, and token (usually the same as Confluence)
- Which port to use for the MCP server (default: `8080`, press Enter to accept)

**Step 4 — Writes `mcp/.env`**
Creates the credentials file from your answers. Reports: `✅ Credentials saved to mcp/.env`

**Step 5 — Installs Python dependencies**
Runs `uv sync` inside `mcp/` to install all required packages. Reports: `✅ Dependencies installed`

**Step 6 — Prompts you to start the MCP server**
Gives you the exact command to run in a second terminal (see [Step 5 below](#5-start-the-mcp-server)) and waits for you to confirm it is running before continuing.

**Step 7 — Registers the MCP server with Codemie**
Runs `codemie-claude mcp add` to connect Codemie to the local MCP server. If automatic registration fails, it gives you the manual fallback (see [Manual configuration reference](#8-manual-configuration-reference)).

**Step 8 — Prompts you to restart Codemie**
The MCP connection only takes effect after a restart. The wizard tells you how to restart (`/exit` then relaunch with `codemie-claude`) and reminds you to run `/setup verify` afterwards.

> **Re-running /setup**
> You can run `/setup` again at any time to update credentials, change the port, or add a new integration. It detects the existing `.env` and asks before overwriting.

---

## 5. Start the MCP server

The `/setup` wizard will prompt you to do this at the right moment (Step 6 of the wizard), but here is the command for reference.

Open a **dedicated second terminal** and keep it running throughout your session:

```bash
cd "C:\Users\[your_user]\Documents\MSC-BA-agent\mcp"
uv run msc-mcp-server
```

> **Mac/Linux:**
> ```bash
> cd ~/Documents/MSC-BA-agent/mcp
> uv run msc-mcp-server
> ```

**Expected output:**
```
Starting MSC MCP Server on 0.0.0.0:8080 (transport=streamable-http)
Application startup complete.
```

Once you see this, go back to the `/setup` wizard in your Claude Code terminal and type `ready` to continue.

**Do not close this terminal.** The server runs in the foreground. Closing it stops all Jira and Confluence tools until you restart it.

> **Port already in use?**
> If you see a port conflict error, either a previous MCP server session is still running (reuse it — no restart needed) or another process has taken port 8080. To change the port, run `/setup` again and enter a different port number when prompted.

---

## 6. Restart Claude Code and verify

After the `/setup` wizard completes, restart Codemie so the MCP server connection takes effect:

- **Terminal (CLI):** type `/exit`, then relaunch with `codemie-claude` from the project root
- **Desktop app:** press `Ctrl+R` (Windows/Linux) or `Cmd+R` (Mac)
- **VS Code extension:** open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and run `Codemie: Restart`

Once restarted, run the verification command:

```
/setup verify
```

The verify mode will:
1. Call `hello_world` on the MCP server — confirms the server is reachable
2. Call `health_check` — shows which integrations are active
3. Ask for a Confluence page ID to confirm live read access (you can skip this if you do not have one to hand)
4. Print a ready summary, e.g.:

```
🎉 MSC BA Agent is ready!

✅ MCP server connected (port 8080)
✅ Confluence connected (https://msccruises.atlassian.net)
✅ Jira connected
```

If the MCP server is not reachable, check that the server terminal (Step 5) is still running and has not errored.

Once `/setup verify` passes, you are fully set up. Type `/ba-workflow` to start.

> **Reminder:** always launch Codemie using `codemie-claude`, not `claude`. See the note at the top of this guide.

---

## 7. Your daily workflow

Every time you start a new working session, you only need two commands:

**Terminal 1 — Start the MCP server (keep open):**
```bash
cd "C:\Users\[your_user]\Documents\MSC-BA-agent\mcp"
uv run msc-mcp-server
```

**Terminal 2 — Open Claude Code:**
```bash
cd "C:\Users\[your_user]\Documents\MSC-BA-agent"
codemie-claude
```

**In Claude Code:**
```
/ba-workflow
```

> You do not need to re-run `/setup` each session. Credentials are stored in `mcp/.env` and persist between sessions. Only re-run `/setup` if your API token expires or you want to update your configuration.

---

## 8. Manual configuration reference

If the `/setup` wizard cannot complete a step automatically, here is how to do each part by hand.

### Manually create mcp/.env

```bash
cd mcp
cp .env.example .env    # Mac/Linux
copy .env.example .env  # Windows Command Prompt
```

Open `mcp/.env` and fill in:

```
MSC_HOST=0.0.0.0
MSC_PORT=8080
MSC_TRANSPORT=sse

MSC_JIRA_URL=https://msccruises.atlassian.net
MSC_JIRA_EMAIL=your.name@msccruises.com
MSC_JIRA_TOKEN=your-api-token

MSC_CONFLUENCE_URL=https://msccruises.atlassian.net
MSC_CONFLUENCE_EMAIL=your.name@msccruises.com
MSC_CONFLUENCE_TOKEN=your-api-token
```

`MSC_JIRA_TOKEN` and `MSC_CONFLUENCE_TOKEN` are the same Atlassian API token. The remaining variables (`MSC_ANYPOINT_*`, `MSC_GIT_*`, `MSC_MS_*`) are optional integrations — leave blank if not needed.

### Manually install dependencies

```bash
cd mcp
uv sync
```

### Manually register the MCP server with Codemie

```bash
codemie-claude mcp add msc-ba --transport http http://localhost:8080/mcp
```

Or add it directly to `~/.claude/settings.json` (Windows: `C:\Users\[your_user]\.claude\settings.json`):

```json
{
  "mcpServers": {
    "msc-ba": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

Verify it was added: `codemie-claude mcp list`

---

## 9. Troubleshooting

### "uv: command not found"

uv was not added to your PATH during installation.

- **Windows:** Use the full path:
  ```bash
  C:\Users\[your_user]\AppData\Roaming\Python\Python312\Scripts\uv.exe run msc-mcp-server
  ```
  Or reinstall: `pip install uv` and open a new terminal.

- **Mac/Linux:**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source ~/.bashrc  # or source ~/.zshrc
  ```

---

### "Python version too old" or "python: command not found"

The MCP server requires Python 3.12+. Check:
```bash
python --version
python3 --version
```

If neither returns 3.12 or later, download from https://www.python.org/downloads/ and ensure **"Add to PATH"** is ticked. Then tell uv to use that version:
```bash
uv python install 3.12
```

---

### MCP server starts but `/setup verify` says tools are not available

1. Confirm the server terminal shows `Application startup complete.`
2. Confirm MCP registration: `codemie-claude mcp list` — check `msc-ba` is listed at `http://localhost:8080/mcp`
3. Restart Codemie (`/exit` then `codemie-claude`) — the MCP connection only activates after a restart
4. If you changed the port in `.env`, update the registered URL to match (re-run `/setup` or edit `settings.json` manually)

---

### "401 Unauthorized" or "403 Forbidden" from Confluence or Jira

Your API token has expired or is incorrect.

1. Go to https://id.atlassian.com/manage/api-tokens, revoke the old token and create a new one
2. Run `/setup` again — choose to re-configure when prompted — and enter the new token
3. Restart the MCP server

Also confirm that your email in `mcp/.env` exactly matches the Atlassian account that owns the token.

---

### `/setup` or `/ba-workflow` is not recognised

Codemie must be launched from the project root — the folder containing `CLAUDE.md` and the `agents/` directory. If you launched from a different folder, the custom commands will not load. Also confirm you are using `codemie-claude`, not the standard `claude` CLI.

```bash
cd "C:\Users\[your_user]\Documents\MSC-BA-agent"
codemie-claude
```

---

### Port 8080 is already in use

A previous session's MCP server is likely still running — you can reuse it without restarting.

To free the port if needed:
- **Windows:** Open Task Manager → find the `python` process on port 8080 → End task
- **Mac/Linux:** `lsof -ti:8080 | xargs kill`

Alternatively, run `/setup` and choose a different port (e.g. `8081`).
