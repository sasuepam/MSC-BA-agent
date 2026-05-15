# MSC BA MCP Server

MCP server for the MSC Mule BA Agent — provides Jira and Confluence tools to Codemie for DTTP BA workflows.

## Tools available

| Tool | Description |
|------|-------------|
| `confluence_get_markdown` | Read any Confluence page as clean Markdown |
| `confluence_get_page` | Read a Confluence page (plain text) |
| `confluence_search` | Search Confluence by text or title |
| `confluence_get_space_pages` | List all pages in a space |
| `confluence_get_child_pages` | Navigate the Confluence page tree |
| `confluence_create_page` | Create a new page (sandbox by default) |
| `confluence_update_page` | Update an existing page |
| `confluence_extract_ia` | Parse IA/PAPI pages into structured JSON |
| `jira_get_issue` | Read a Jira issue by key |
| `jira_search` | Search issues with JQL |
| `jira_create_issue` | Create a new Jira issue |
| `jira_update_issue` | Update an existing issue |
| `jira_add_comment` | Add a comment to an issue |
| `jira_get_projects` | List available Jira projects |
| `hello_world` | Test MCP connection |
| `health_check` | Server health status |

## Setup

See `../docs/SETUP.md` for full setup instructions.
