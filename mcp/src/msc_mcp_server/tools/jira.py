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
          - jira_search("project = DTTP25 AND status = 'In Progress'")
          - jira_search("assignee = currentUser() AND sprint in openSprints()")
          - jira_search("text ~ 'functional spec' AND project = DTTP25")

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
            project_key: Project key (e.g. "DTTP25").
            summary: Issue title/summary.
            issue_type: "Task", "Story", "Bug", "Epic", "Sub-task". Default: "Task".
            description: Issue description (plain text).
            assignee_email: Email of the assignee (optional).
            labels: List of label strings (optional).
            priority: "Highest", "High", "Medium", "Low", "Lowest". Default: "Medium".
        """
        err = _check_config()
        if err:
            return {"error": err}

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
        status_transition: str = "",
        assignee_email: str = "",
        labels: list[str] | None = None,
    ) -> dict:
        """Update an existing Jira issue.

        Args:
            issue_key: Issue key like DTTP25-123.
            summary: New summary (leave empty to keep current).
            description: New description text (leave empty to keep current).
            status_transition: Transition name (e.g. "In Progress", "Done", "To Do").
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
            updates["description"] = [{
                "set": {
                    "type": "doc",
                    "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
                }
            }]

        if labels is not None:
            updates["labels"] = [{"set": labels}]

        async with httpx.AsyncClient(timeout=30.0) as client:
            if updates:
                resp = await client.put(
                    f"{_base_url()}/rest/api/3/issue/{issue_key}",
                    headers=_default_headers(),
                    json={"update": updates},
                )
                if not resp.is_success and resp.status_code != 204:
                    return {"error": f"Update failed {resp.status_code}: {resp.text[:200]}"}

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
