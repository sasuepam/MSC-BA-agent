"""Jira tools — create, search, update issues.

Uses the Jira Cloud REST API v3.
Authentication: HTTP Basic Auth (Atlassian email + API token).
"""

import base64
import logging

import httpx
from mcp.server.fastmcp import FastMCP

from msc_mcp_server.config import settings

logger = logging.getLogger(__name__)


def _auth_header() -> str:
    credentials = f"{settings.jira_email}:{settings.jira_token}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def _base_url() -> str:
    return settings.jira_url.rstrip("/")


def _check_config() -> str | None:
    if not settings.jira_url:
        return "Jira not configured — set MSC_JIRA_URL in .env (e.g. https://yourcompany.atlassian.net)"
    if not settings.jira_email:
        return "Jira not configured — set MSC_JIRA_EMAIL in .env"
    if not settings.jira_token:
        return "Jira not configured — set MSC_JIRA_TOKEN in .env"
    return None


def _default_headers() -> dict:
    return {
        "Authorization": _auth_header(),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _text_to_adf(text: str) -> dict:
    """Convert structured plain text to Atlassian Document Format (ADF).

    Supports:
      ## Heading text   → ADF heading level 2
      - Bullet item     → ADF bulletList item
      Plain text        → ADF paragraph
    Blank lines flush any buffered paragraph or bullet list.
    """
    if not text:
        return {"type": "doc", "version": 1, "content": []}

    content: list = []
    bullet_buffer: list = []
    para_buffer: list = []

    def flush_para() -> None:
        if para_buffer:
            content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": " ".join(para_buffer)}],
            })
            para_buffer.clear()

    def flush_bullets() -> None:
        if bullet_buffer:
            content.append({"type": "bulletList", "content": list(bullet_buffer)})
            bullet_buffer.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            flush_para()
            flush_bullets()
        elif stripped.startswith("## "):
            flush_para()
            flush_bullets()
            content.append({
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": stripped[3:].strip()}],
            })
        elif stripped.startswith("- "):
            flush_para()
            bullet_buffer.append({
                "type": "listItem",
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": stripped[2:].strip()}],
                }],
            })
        else:
            flush_bullets()
            para_buffer.append(stripped)

    flush_para()
    flush_bullets()

    return {"type": "doc", "version": 1, "content": content}


def register(mcp: FastMCP) -> None:
    """Register Jira tools on the MCP server instance."""

    @mcp.tool()
    async def jira_get_issue(issue_key: str) -> dict:
        """Get a Jira issue by its key (e.g. DTTP25-31070).

        Returns the issue summary, description, status, assignee, labels,
        and any linked issues or Confluence pages.

        Args:
            issue_key: Jira issue key like PROJECT-123.
        """
        err = _check_config()
        if err:
            return {"error": err}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{_base_url()}/rest/api/3/issue/{issue_key}",
                headers=_default_headers(),
                params={"fields": "summary,description,status,assignee,reporter,labels,priority,issuetype,project,comment,attachment"},
            )

        if resp.status_code == 404:
            return {"error": f"Issue '{issue_key}' not found"}
        if resp.status_code == 401:
            return {"error": "Authentication failed — check MSC_JIRA_EMAIL and MSC_JIRA_TOKEN"}
        if not resp.is_success:
            return {"error": f"Jira API error {resp.status_code}: {resp.text[:200]}"}

        data = resp.json()
        fields = data.get("fields", {})

        # Extract description text
        desc = fields.get("description", {})
        desc_text = ""
        if isinstance(desc, dict):
            for block in desc.get("content", []):
                for inner in block.get("content", []):
                    if inner.get("type") == "text":
                        desc_text += inner.get("text", "") + " "

        return {
            "key": data.get("key"),
            "summary": fields.get("summary"),
            "status": fields.get("status", {}).get("name"),
            "issue_type": fields.get("issuetype", {}).get("name"),
            "priority": fields.get("priority", {}).get("name"),
            "project": fields.get("project", {}).get("name"),
            "assignee": (fields.get("assignee") or {}).get("displayName"),
            "reporter": (fields.get("reporter") or {}).get("displayName"),
            "labels": fields.get("labels", []),
            "description": desc_text.strip()[:1000],
            "url": f"{_base_url()}/browse/{data.get('key')}",
        }

    @mcp.tool()
    async def jira_search(jql: str, limit: int = 10) -> dict:
        """Search Jira issues using JQL (Jira Query Language).

        Examples:
          - jira_search("project = DTTP AND status = 'In Progress'")
          - jira_search("assignee = currentUser() AND sprint in openSprints()")
          - jira_search("text ~ 'Klarna' AND project = DTTP25")

        Args:
            jql: JQL query string.
            limit: Max results to return (1-50).
        """
        err = _check_config()
        if err:
            return {"error": err}

        limit = max(1, min(limit, 50))

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_base_url()}/rest/api/3/issue/search",
                headers=_default_headers(),
                json={
                    "jql": jql,
                    "maxResults": limit,
                    "fields": ["summary", "status", "assignee", "priority", "issuetype"],
                },
            )

        if resp.status_code == 400:
            return {"error": f"Invalid JQL: {resp.text[:200]}"}
        if resp.status_code == 401:
            return {"error": "Authentication failed"}
        if not resp.is_success:
            return {"error": f"Jira API error {resp.status_code}: {resp.text[:200]}"}

        data = resp.json()
        issues = []
        for issue in data.get("issues", []):
            f = issue.get("fields", {})
            issues.append({
                "key": issue.get("key"),
                "summary": f.get("summary"),
                "status": f.get("status", {}).get("name"),
                "assignee": (f.get("assignee") or {}).get("displayName"),
                "priority": f.get("priority", {}).get("name"),
                "type": f.get("issuetype", {}).get("name"),
                "url": f"{_base_url()}/browse/{issue.get('key')}",
            })

        return {
            "total": data.get("total", len(issues)),
            "returned": len(issues),
            "issues": issues,
        }

    @mcp.tool()
    async def jira_create_issue(
        project_key: str,
        summary: str,
        issue_type: str = "Task",
        description: str = "",
        assignee_email: str = "",
        labels: list[str] | None = None,
        priority: str = "Medium",
    ) -> dict:
        """Create a new Jira issue.

        Args:
            project_key: Project key (e.g. "DTTP25", "TEST").
            summary: Issue title/summary.
            issue_type: "Task", "Story", "Bug", "Epic", "Sub-task". Default: "Task".
            description: Issue description text (plain text, will be converted to Jira doc format).
            assignee_email: Email of the assignee (optional).
            labels: List of label strings (optional).
            priority: "Highest", "High", "Medium", "Low", "Lowest". Default: "Medium".

        Returns:
            Created issue key, ID, and URL.
        """
        err = _check_config()
        if err:
            return {"error": err}

        # Build description in Atlassian Document Format
        desc_doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}],
                }
            ] if description else [],
        }

        fields: dict = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
            "description": desc_doc,
        }

        if labels:
            fields["labels"] = labels

        if assignee_email:
            # Look up accountId by email
            async with httpx.AsyncClient(timeout=30.0) as client:
                user_resp = await client.get(
                    f"{_base_url()}/rest/api/3/user/search",
                    headers=_default_headers(),
                    params={"query": assignee_email},
                )
                if user_resp.is_success:
                    users = user_resp.json()
                    if users:
                        fields["assignee"] = {"accountId": users[0]["accountId"]}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_base_url()}/rest/api/3/issue",
                headers=_default_headers(),
                json={"fields": fields},
            )

        if resp.status_code == 400:
            return {"error": f"Bad request: {resp.text[:300]}"}
        if resp.status_code == 401:
            return {"error": "Authentication failed"}
        if resp.status_code == 403:
            return {"error": "Permission denied — check project permissions"}
        if not resp.is_success:
            return {"error": f"Jira API error {resp.status_code}: {resp.text[:300]}"}

        data = resp.json()
        return {
            "key": data.get("key"),
            "id": data.get("id"),
            "url": f"{_base_url()}/browse/{data.get('key')}",
        }

    @mcp.tool()
    async def jira_update_issue(
        issue_key: str,
        summary: str = "",
        description: str = "",
        acceptance_criteria: str = "",
        status_transition: str = "",
        assignee_email: str = "",
        labels: list[str] | None = None,
    ) -> dict:
        """Update an existing Jira issue.

        Can update summary, description, acceptance criteria, assignee, labels.
        To change status use status_transition (e.g. "In Progress", "Done").

        Description and acceptance_criteria support structured plain text:
          ## Section heading  → renders as H2
          - Bullet item       → renders as a bullet list item

        Args:
            issue_key: Issue key like DTTP25-123.
            summary: New summary (leave empty to keep current).
            description: New description text (leave empty to keep current).
            acceptance_criteria: Acceptance criteria text (leave empty to keep current).
                Stored in the custom field configured via MSC_JIRA_AC_FIELD.
            status_transition: Transition name to move issue to (e.g. "In Progress", "Done", "To Do").
            assignee_email: New assignee email (leave empty to keep current).
            labels: New labels list (replaces existing labels).
        """
        err = _check_config()
        if err:
            return {"error": err}

        updates: dict = {}

        if summary:
            updates["summary"] = [{"set": summary}]

        if description:
            updates["description"] = [{"set": _text_to_adf(description)}]

        if acceptance_criteria:
            ac_field = settings.jira_ac_field
            if ac_field:
                updates[ac_field] = [{"set": _text_to_adf(acceptance_criteria)}]
            else:
                # No AC field configured — append AC block to description
                ac_suffix = "\n\n## Acceptance Criteria\n" + acceptance_criteria
                combined = (description + ac_suffix) if description else ac_suffix
                updates["description"] = [{"set": _text_to_adf(combined)}]

        if labels is not None:
            updates["labels"] = [{"set": labels}]

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Update fields
            if updates:
                resp = await client.put(
                    f"{_base_url()}/rest/api/3/issue/{issue_key}",
                    headers=_default_headers(),
                    json={"update": updates},
                )
                if not resp.is_success and resp.status_code != 204:
                    return {"error": f"Update failed {resp.status_code}: {resp.text[:200]}"}

            # Handle status transition
            if status_transition:
                trans_resp = await client.get(
                    f"{_base_url()}/rest/api/3/issue/{issue_key}/transitions",
                    headers=_default_headers(),
                )
                if trans_resp.is_success:
                    transitions = trans_resp.json().get("transitions", [])
                    match = next(
                        (t for t in transitions if t["name"].lower() == status_transition.lower()),
                        None
                    )
                    if match:
                        await client.post(
                            f"{_base_url()}/rest/api/3/issue/{issue_key}/transitions",
                            headers=_default_headers(),
                            json={"transition": {"id": match["id"]}},
                        )
                    else:
                        available = [t["name"] for t in transitions]
                        return {"warning": f"Transition '{status_transition}' not found. Available: {available}"}

        return {"success": True, "key": issue_key, "url": f"{_base_url()}/browse/{issue_key}"}

    @mcp.tool()
    async def jira_add_comment(issue_key: str, comment: str) -> dict:
        """Add a comment to a Jira issue.

        Args:
            issue_key: Issue key like DTTP25-123.
            comment: Comment text (plain text).
        """
        err = _check_config()
        if err:
            return {"error": err}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_base_url()}/rest/api/3/issue/{issue_key}/comment",
                headers=_default_headers(),
                json={
                    "body": {
                        "type": "doc",
                        "version": 1,
                        "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}],
                    }
                },
            )

        if not resp.is_success:
            return {"error": f"Jira API error {resp.status_code}: {resp.text[:200]}"}

        data = resp.json()
        return {
            "id": data.get("id"),
            "url": f"{_base_url()}/browse/{issue_key}",
        }

    @mcp.tool()
    async def jira_get_projects(limit: int = 20) -> dict:
        """List available Jira projects.

        Useful for discovering project keys before creating issues.
        """
        err = _check_config()
        if err:
            return {"error": err}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{_base_url()}/rest/api/3/project/search",
                headers=_default_headers(),
                params={"maxResults": min(limit, 50)},
            )

        if not resp.is_success:
            return {"error": f"Jira API error {resp.status_code}: {resp.text[:200]}"}

        data = resp.json()
        return {
            "projects": [
                {
                    "key": p.get("key"),
                    "name": p.get("name"),
                    "type": p.get("projectTypeKey"),
                }
                for p in data.get("values", [])
            ]
        }
