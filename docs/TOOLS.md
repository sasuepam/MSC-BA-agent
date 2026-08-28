# Tools Reference

All tools available in the MSC API Designer assistant.

---

## Slash Commands

Type these in Claude Code at any time. Claude also activates the right workflow automatically from natural language — the slash commands are shortcuts.

### Setup & Configuration

| Command | What it does |
|---------|-------------|
| `/setup` | First-time environment wizard. Collects credentials, writes `.env`, tests connection. |

### Core Design Workflows

| Command | What it does | When to use |
|---------|-------------|-------------|
| `/generate` | Generate full page set: MUL + EAPI + PAPI + SAPI | New endpoint from scratch |
| `/validate` | Cross-check all pages against the IA | After generation, after any change |
| `/update` | Change a field in one or more pages | Single targeted edit |
| `/propagate` | Push a field change across all 4 pages simultaneously | When IA changes a field |
| `/diff` | Compare two page versions or a page vs IA | Quality check, version comparison |

### Design Process Steps

| Command | What it does | Process step |
|---------|-------------|-------------|
| `/import-ia` | Extract and preview IA data before generating | Before Step 1 |
| `/status` | Show 6-step design progress for an interface | Anytime |
| `/preview` | Render generated HTML in browser before publishing | Before any Confluence write |
| `/raml` | Generate RAML specification files | Step 2 & 5 |
| `/hla` | Generate HLA page with sequence diagram | Step 3 |
| `/jira` | Create Jira implementation subtasks | Step 6 |

### Knowledge & Q&A

| Command | What it does |
|---------|-------------|
| `/explain` | Answer any question about MSC API conventions |

---

## MCP Tools (Confluence + Jira)

These are the tools Claude calls automatically. You don't invoke them directly — Claude does.

### Confluence

| Tool | What it does | When Claude uses it |
|------|-------------|-------------------|
| `confluence_get_markdown(page_id)` | Reads any page as clean Markdown (70-97% smaller than HTML) | Before every edit |
| `confluence_extract_ia(page_id)` | Deterministic IA table parser → structured JSON | Field extraction from IA/MUL |
| `confluence_create_page(title, parent_id, content, space_key, instance)` | Creates new page in sandbox or production | After generation is approved |
| `confluence_update_page(page_id, title, content, version)` | Updates existing page | After edit is approved |
| `confluence_search(query)` | Full-text search | Finding pages by interface ID |
| `confluence_get_page(page_id)` | Raw HTML (rarely needed) | Edge cases only |

### Jira

| Tool | What it does | When Claude uses it |
|------|-------------|-------------------|
| `jira_search(jql)` | Search issues by JQL | `/status` and `/jira` |
| `jira_get_issue(key)` | Read issue details | Before creating subtasks |
| `jira_create_issue(...)` | Create new subtask | `/jira` command |

---

## Automated Hooks

These run silently on every Confluence write — you don't need to trigger them.

### Pre-Write Validator (blocks bad writes)
Runs before every `confluence_create_page` or `confluence_update_page`.

Checks for:
- **Blocked MSC headers** — headers that hallucinate from other interfaces
- **Suspicious field names** — known business-name / technical-name swaps
- **Empty sections** — pages with H1 sections but no content

If critical issues found → **write is blocked** and Claude reports what to fix.

### Post-Write Coverage Reporter
Runs after every `confluence_create_page`.

Reports:
- Table row count
- Number of H2/H3 sections
- Any blocked headers that slipped through
- Recommendation to run `/validate`

---

## Confluence Page IDs — Quick Reference

### Sandbox parent IDs (where drafts are created)
| Page type | Parent ID |
|-----------|-----------|
| MUL | `688129` |
| EAPI | `917505` |
| PAPI | `786433` |
| SAPI | `851969` |

### Reference pages (INT004.4 Klarna — working examples)
| Page | ID |
|------|----|
| IA/PAPI source | `4476535093` |
| MUL | `4325507083` |
| EAPI | `4072473378` |
| SAPI | `4156620801` |
