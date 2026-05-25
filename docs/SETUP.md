# Setup Guide — MSC Mule BA Agent

A complete walkthrough for getting the MSC Mule BA Agent running on a new machine, from cloning the repository to running your first workflow.

**Estimated time:** 15–20 minutes

---

## Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the repository](#2-clone-the-repository)
3. [Install Python dependencies](#3-install-python-dependencies)
4. [Configure your credentials](#4-configure-your-credentials)
5. [Configure Claude Code](#5-configure-claude-code)
6. [Register the MCP server with Claude Code](#6-register-the-mcp-server-with-claude-code)
7. [Start the MCP server](#7-start-the-mcp-server)
8. [Verify everything works](#8-verify-everything-works)
9. [Your daily workflow](#9-your-daily-workflow)
10. [Troubleshooting](#10-troubleshooting)

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

### Claude Code
The AI coding assistant that runs the BA agents.
- Download and install from https://claude.ai/code
- Follow the Claude Code installer instructions for your operating system
- **Verify:** `claude --version` or `codemie-claude --version`

### Atlassian API token
Required to connect to Jira and Confluence. You will need this in Step 4.
- Go to https://id.atlassian.com/manage/api-tokens
- Click **Create API token**
- Give it a label (e.g. `MSC BA Agent`) and copy the token — you will not be able to see it again

---

## 2. Clone the repository

Open a terminal and clone the repository to your machine.

```bash
git clone https://github.com/sasuepam/MSC-BA-agent.git
```

This creates a folder called `MSC-BA-agent` in your current directory. Navigate into the project:

```bash
cd MSC-BA-agent
```

> **Windows users:** If you prefer a specific location (e.g. your Documents folder), navigate there first:
> ```bash
> cd "C:\Users\[your_user]\Documents"
> git clone https://github.com/sasuepam/MSC-BA-agent.git
> cd MSC-BA-agent
> ```

Your project root should now contain:
```
MSC-BA-agent/
├── agents/
├── docs/
├── knowledge/
├── mcp/
├── output/
├── .claude/
├── CLAUDE.md
└── README.md
```

---

## 3. Install Python dependencies

The MCP server (which connects Claude to Jira and Confluence) has its own Python dependencies. Install them with:

```bash
cd mcp
uv sync
```

`uv sync` reads `pyproject.toml` and installs all required packages into an isolated virtual environment inside the `mcp/` folder. You do not need to activate the environment manually — `uv run` handles that automatically.

**Expected output:**
```
Resolved X packages
Installed X packages
```

If you see errors, check that Python 3.12+ is installed and accessible on your PATH.

---

## 4. Configure your credentials

The MCP server needs your Atlassian credentials to talk to Jira and Confluence. These are stored in a local `.env` file that is never committed to Git.

From inside the `mcp/` folder (you should already be there from Step 3):

```bash
cp .env.example .env
```

> **Windows (Command Prompt):**
> ```bash
> copy .env.example .env
> ```

Open `mcp/.env` in any text editor and fill in your values:

```
# --- Server (leave as-is unless port 8080 is already in use) ---
MSC_HOST=0.0.0.0
MSC_PORT=8080
MSC_TRANSPORT=sse
MSC_DEBUG=false
MSC_SERVER_NAME=msc-mcp-server

# --- Jira ---
MSC_JIRA_URL=https://msccruises.atlassian.net
MSC_JIRA_EMAIL=your.name@msccruises.com
MSC_JIRA_TOKEN=your-api-token-here

# --- Confluence ---
MSC_CONFLUENCE_URL=https://msccruises.atlassian.net
MSC_CONFLUENCE_EMAIL=your.name@msccruises.com
MSC_CONFLUENCE_TOKEN=your-api-token-here
```

**Notes:**
- `MSC_JIRA_TOKEN` and `MSC_CONFLUENCE_TOKEN` are both set to the **same Atlassian API token** you generated in Step 1 — one token covers both products
- `MSC_JIRA_URL` and `MSC_CONFLUENCE_URL` are both your Atlassian domain (no `/wiki` or `/jira` suffix needed)
- The remaining variables (`MSC_ANYPOINT_*`, `MSC_GIT_*`, `MSC_MS_*`) are for optional integrations — leave them blank unless you are setting those up
- **Never commit `.env`** — it is already listed in `.gitignore`

---

## 5. Configure Claude Code

Claude Code needs to know where the project lives and which custom instructions to load.

Navigate back to the project root (one level up from `mcp/`):

```bash
cd ..
```

You should now be in the `MSC-BA-agent/` root directory.

Claude Code automatically reads `CLAUDE.md` from the project root when you launch it from this folder. This file contains all the MSC BA conventions, pipeline instructions, and agent definitions. **No manual configuration of CLAUDE.md is needed.**

The `.claude/` folder contains the custom skills (`/ba-workflow`, `/ba-amend`) and project-level settings. These are already configured in the repository.

---

## 6. Register the MCP server with Claude Code

Claude Code needs to know the address of the local MCP server so it can call the Jira and Confluence tools.

Run this **once** from any terminal:

```bash
claude mcp add msc-ba --transport http http://localhost:8080/mcp
```

This adds the MCP server to your **global** Claude Code settings so it is available in all projects.

**To verify it was added:**
```bash
claude mcp list
```

You should see `msc-ba` listed with the URL `http://localhost:8080/mcp`.

**Alternative — add it manually:**

If the `claude mcp add` command is not available, open your Claude Code settings file:
- **Windows:** `C:\Users\[your_user]\.claude\settings.json`
- **Mac/Linux:** `~/.claude/settings.json`

Add the following (create the file if it does not exist):

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

## 7. Start the MCP server

The MCP server must be running whenever you use the BA agents. It is what allows Claude to read Confluence pages, fetch Jira tickets, and push updates.

Open a **dedicated terminal** for the server (keep it open throughout your session):

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

**Do not close this terminal.** The server runs in the foreground. If you close it, the Jira and Confluence tools will stop working until you restart it.

> **Port already in use?** If you see an error about port 8080, either a previous MCP server session is still running (no action needed — reuse it) or another process has taken the port. To use a different port, change `MSC_PORT=8080` in `mcp/.env` to an unused port (e.g. `8081`) and update the Claude Code MCP URL in Step 6 to match.

---

## 8. Verify everything works

Open a **second terminal** (leave the MCP server running in the first one) and launch Claude Code from the project root:

```bash
cd "C:\Users\[your_user]\Documents\MSC-BA-agent"
codemie-claude
```

> **Mac/Linux:**
> ```bash
> cd ~/Documents/MSC-BA-agent
> claude
> ```

Once Claude Code is open, send this message:

```
hello, can you check if the MCP server is connected?
```

Claude should respond with a confirmation that the MCP server is reachable. If it does, setup is complete.

**Then run a quick end-to-end check:**

```
/ba-workflow
```

You should see the workflow menu:

```
1. Spec only
2. Stories only
3. Full end-to-end
4. Validate and publish
```

If the menu appears, the agents, skills, and CLAUDE.md are all loaded correctly.

---

## 9. Your daily workflow

Every time you start a new working session:

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

Choose your option and follow the prompts.

> The `uv sync` and `claude mcp add` steps from setup only need to be run once. You do not need to repeat them each session.

---

## 10. Troubleshooting

### "uv: command not found"

uv was not added to your PATH during installation.

- **Windows:** Use the full path:
  ```bash
  C:\Users\[your_user]\AppData\Roaming\Python\Python312\Scripts\uv.exe run msc-mcp-server
  ```
  Or reinstall uv: `pip install uv` and restart your terminal.

- **Mac/Linux:**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source ~/.bashrc  # or source ~/.zshrc
  ```

---

### "python: command not found" or wrong Python version

Check which Python version is active:
```bash
python --version
python3 --version
```

If neither returns 3.12 or later, download the latest Python from https://www.python.org/downloads/ and ensure **"Add to PATH"** is ticked during installation.

---

### MCP server starts but Claude says tools are not available

1. Confirm the server is running — check the MCP server terminal for the `Application startup complete.` message
2. Confirm the MCP registration — run `claude mcp list` and check `msc-ba` is listed
3. Restart Claude Code — close the Claude terminal and reopen it
4. If you changed the port in `.env`, make sure the URL in `claude mcp list` matches

---

### "401 Unauthorized" or "403 Forbidden" from Confluence or Jira

Your API token has either expired or is incorrect.

1. Go to https://id.atlassian.com/manage/api-tokens
2. Revoke the old token and create a new one
3. Open `mcp/.env` and replace `MSC_JIRA_TOKEN` and `MSC_CONFLUENCE_TOKEN` with the new token
4. Restart the MCP server

Also check that `MSC_JIRA_EMAIL` and `MSC_CONFLUENCE_EMAIL` match the Atlassian account that owns the token exactly.

---

### `/ba-workflow` does nothing or is not recognised

Claude Code must be launched from the project root — the folder that contains `CLAUDE.md` and the `agents/` directory:

```bash
cd "C:\Users\[your_user]\Documents\MSC-BA-agent"
codemie-claude
```

If you launched Claude Code from a different directory, the custom skills and CLAUDE.md will not be loaded.

---

### Port 8080 is already in use

If you see a port conflict error when starting the MCP server, check whether a previous session's server is still running. If it is, you can reuse it — no need to restart.

To kill the existing process and restart:
- **Windows:** Open Task Manager, find the `python` process using port 8080, and end it
- **Mac/Linux:** `lsof -ti:8080 | xargs kill`

---

### "uv sync" fails with a build error

Make sure you have Python 3.12+ installed. The `pyproject.toml` requires `requires-python = ">=3.12"`.

Check the version uv is using:
```bash
uv python list
```

If 3.12 is not listed, install it:
```bash
uv python install 3.12
```
