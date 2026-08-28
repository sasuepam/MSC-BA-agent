"""Confluence tools — read pages, search content, navigate spaces.

Uses the Confluence Cloud REST API:
  - v2 API for page operations: /wiki/api/v2/...
  - v1 API for CQL search:      /wiki/rest/api/search  (no v2 equivalent yet)

Authentication: HTTP Basic Auth (Atlassian email + API token).
Generate a token at: https://id.atlassian.com/manage/api-tokens
"""

import base64
import logging
import re
from html.parser import HTMLParser

import httpx
from mcp.server.fastmcp import FastMCP

from msc_mcp_server.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_header() -> str:
    """Build the Basic auth header value from configured email + API token."""
    credentials = f"{settings.confluence_email}:{settings.confluence_token}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def _base_url() -> str:
    """Return the Confluence base URL with no trailing slash."""
    return settings.confluence_url.rstrip("/")


def _check_config() -> str | None:
    """Return an error message if Confluence credentials are not configured, else None."""
    if not settings.confluence_url:
        return "Confluence not configured — set MSC_CONFLUENCE_URL in .env (e.g. https://yourcompany.atlassian.net)"
    if not settings.confluence_email:
        return "Confluence not configured — set MSC_CONFLUENCE_EMAIL in .env"
    if not settings.confluence_token:
        return "Confluence not configured — set MSC_CONFLUENCE_TOKEN in .env (API token from id.atlassian.com)"
    return None


def _strip_html(html: str) -> str:
    """Strip Confluence storage-format HTML/XML tags and return clean plain text."""

    class _Stripper(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts: list[str] = []

        def handle_data(self, data: str) -> None:
            self.parts.append(data)

    stripper = _Stripper()
    stripper.feed(html)
    text = " ".join(stripper.parts)
    # Collapse runs of whitespace / newlines into single spaces
    return re.sub(r"\s+", " ", text).strip()


def _default_headers() -> dict:
    return {"Authorization": _auth_header(), "Accept": "application/json"}


def _get_write_config(instance: str) -> tuple[str, str] | None:
    """Return (base_url, auth_header) for the given write instance.

    instance = "sandbox" → uses MSC_CONFLUENCE_SANDBOX_* settings
    instance = "prod"    → uses MSC_CONFLUENCE_* settings (careful!)

    Returns None if the requested instance is not configured.
    """
    if instance == "sandbox":
        url = settings.confluence_sandbox_url.rstrip("/")
        email = settings.confluence_sandbox_email
        token = settings.confluence_sandbox_token
        if not url or not email or not token:
            return None
        auth = "Basic " + __import__("base64").b64encode(f"{email}:{token}".encode()).decode()
        return url, auth
    else:
        # prod
        url = settings.confluence_url.rstrip("/")
        auth = _auth_header()
        return url, auth


def _check_write_config(instance: str) -> str | None:
    """Return error string if write instance is not configured."""
    if instance == "sandbox":
        if not settings.confluence_sandbox_url:
            return "Sandbox not configured — set MSC_CONFLUENCE_SANDBOX_URL, MSC_CONFLUENCE_SANDBOX_EMAIL, MSC_CONFLUENCE_SANDBOX_TOKEN in .env"
        if not settings.confluence_sandbox_email or not settings.confluence_sandbox_token:
            return "Sandbox credentials incomplete — check MSC_CONFLUENCE_SANDBOX_EMAIL and MSC_CONFLUENCE_SANDBOX_TOKEN"
    return _check_config()


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

def register(mcp: FastMCP) -> None:
    """Register Confluence tools on the MCP server instance."""

    @mcp.tool()
    async def confluence_get_page(page_id: str, include_body: bool = True) -> dict:
        """Get a Confluence page by its numeric page ID.

        Returns the page title, metadata, direct URL, and — when include_body
        is True — the full page content as plain text (HTML tags stripped).

        The page_id is the number visible in the Confluence URL, e.g.
        https://yourcompany.atlassian.net/wiki/spaces/DEV/pages/123456789
                                                                 ^^^^^^^^^
        Use confluence_search or confluence_get_space_pages to discover IDs.
        """
        err = _check_config()
        if err:
            return {"error": err}

        params = {"body-format": "storage"} if include_body else {}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{_base_url()}/wiki/api/v2/pages/{page_id}",
                headers=_default_headers(),
                params=params,
            )

        if resp.status_code == 404:
            return {"error": f"Page '{page_id}' not found"}
        if resp.status_code == 401:
            return {"error": "Authentication failed — check MSC_CONFLUENCE_EMAIL and MSC_CONFLUENCE_TOKEN"}
        if not resp.is_success:
            return {"error": f"Confluence API error {resp.status_code}: {resp.text}"}

        data = resp.json()
        result: dict = {
            "id": data.get("id"),
            "title": data.get("title"),
            "status": data.get("status"),
            "space_id": data.get("spaceId"),
            "parent_id": data.get("parentId"),
            "created_at": data.get("createdAt"),
            "version": data.get("version", {}).get("number"),
            "url": f"{_base_url()}{data.get('_links', {}).get('webui', '')}",
        }

        if include_body:
            raw_html = data.get("body", {}).get("storage", {}).get("value", "")
            result["content"] = _strip_html(raw_html) if raw_html else "(no content)"

        return result

    @mcp.tool()
    async def confluence_search(query: str, space_key: str = "", limit: int = 10) -> dict:
        """Search Confluence pages by text content or title.

        Searches across all spaces by default, or within a specific space when
        space_key is provided. Returns a list of matching pages with excerpts.

        Examples:
          - confluence_search("MuleSoft deployment guide")
          - confluence_search("API design", space_key="DEV")
          - confluence_search("incident runbook", space_key="OPS", limit=5)

        To read full content of a result, pass its id to confluence_get_page.
        """
        err = _check_config()
        if err:
            return {"error": err}

        # Build CQL query — v1 search API (no v2 equivalent exists yet)
        cql_parts = ["type = page", f'text ~ "{query}"']
        if space_key:
            cql_parts.append(f'space = "{space_key}"')
        cql = " AND ".join(cql_parts)
        limit = max(1, min(limit, 50))

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{_base_url()}/wiki/rest/api/search",
                headers=_default_headers(),
                params={"cql": cql, "limit": limit},
            )

        if resp.status_code == 401:
            return {"error": "Authentication failed — check MSC_CONFLUENCE_EMAIL and MSC_CONFLUENCE_TOKEN"}
        if not resp.is_success:
            return {"error": f"Confluence API error {resp.status_code}: {resp.text}"}

        data = resp.json()
        results = []
        for item in data.get("results", []):
            content = item.get("content", {})
            container = item.get("resultGlobalContainer", {})
            results.append({
                "id": content.get("id"),
                "title": content.get("title"),
                "space": container.get("title"),
                "url": f"{_base_url()}{item.get('url', '')}",
                "excerpt": item.get("excerpt", ""),
                "last_modified": item.get("lastModified"),
            })

        return {
            "query": query,
            "cql": cql,
            "total_results": data.get("totalSize", len(results)),
            "returned": len(results),
            "results": results,
        }

    @mcp.tool()
    async def confluence_get_space_pages(space_key: str, limit: int = 25) -> dict:
        """List pages in a Confluence space by its space key.

        Returns page titles and IDs for navigation — use confluence_get_page
        to fetch full content for any page in the list.

        The space_key is the short identifier shown in Confluence URLs, e.g.:
          https://yourcompany.atlassian.net/wiki/spaces/DEV/...
                                                         ^^^  <- this is the key
        """
        err = _check_config()
        if err:
            return {"error": err}

        limit = max(1, min(limit, 250))

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: resolve space key → numeric space ID (required by v2 API)
            space_resp = await client.get(
                f"{_base_url()}/wiki/api/v2/spaces",
                headers=_default_headers(),
                params={"keys": space_key, "limit": 1},
            )
            if not space_resp.is_success:
                return {"error": f"Could not look up space '{space_key}': {space_resp.status_code}"}

            spaces = space_resp.json().get("results", [])
            if not spaces:
                return {"error": f"Space '{space_key}' not found — check the space key is correct"}

            space = spaces[0]
            space_id = space["id"]

            # Step 2: fetch pages in that space
            pages_resp = await client.get(
                f"{_base_url()}/wiki/api/v2/spaces/{space_id}/pages",
                headers=_default_headers(),
                params={"limit": limit, "status": "current"},
            )
            if not pages_resp.is_success:
                return {"error": f"Confluence API error {pages_resp.status_code}: {pages_resp.text}"}

        data = pages_resp.json()
        pages = [
            {
                "id": p.get("id"),
                "title": p.get("title"),
                "parent_id": p.get("parentId"),
            }
            for p in data.get("results", [])
        ]

        return {
            "space_key": space_key,
            "space_name": space.get("name"),
            "pages": pages,
            "returned": len(pages),
            "has_more": "next" in data.get("_links", {}),
        }

    @mcp.tool()
    async def confluence_get_child_pages(page_id: str) -> dict:
        """Get the direct child pages of a Confluence page.

        Use this to navigate the page tree. Given a parent page ID, returns all
        immediate children with their IDs and titles.

        Useful for exploring a section of a space — e.g. find all runbooks under
        an "Operations" parent page, or all API docs under a "Developer Guides" page.
        """
        err = _check_config()
        if err:
            return {"error": err}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{_base_url()}/wiki/api/v2/pages/{page_id}/children",
                headers=_default_headers(),
                params={"limit": 50},
            )

        if resp.status_code == 404:
            return {"error": f"Page '{page_id}' not found"}
        if resp.status_code == 401:
            return {"error": "Authentication failed — check MSC_CONFLUENCE_EMAIL and MSC_CONFLUENCE_TOKEN"}
        if not resp.is_success:
            return {"error": f"Confluence API error {resp.status_code}: {resp.text}"}

        data = resp.json()
        children = [
            {
                "id": p.get("id"),
                "title": p.get("title"),
                "status": p.get("status"),
            }
            for p in data.get("results", [])
        ]

        return {
            "parent_id": page_id,
            "children": children,
            "total": len(children),
            "has_more": "next" in data.get("_links", {}),
        }

    @mcp.tool()
    async def confluence_create_page(
        space_key: str,
        title: str,
        content: str,
        parent_id: str = "",
        status: str = "current",
        instance: str = "sandbox",
    ) -> dict:
        """Create a new Confluence page.

        Creates a page in the specified space. Content must be in Confluence
        storage format (HTML-like markup with <h1>, <table>, <ac:structured-macro> etc).

        Args:
            space_key: The space key (e.g. "DTP", "DEV"). Find it in the Confluence URL.
            title: Page title (must be unique within the space).
            content: Page body in Confluence storage format HTML.
            parent_id: Optional parent page ID. If empty, page is created at space root.
            status: "current" (published) or "draft". Defaults to "current".
            instance: "sandbox" (default, safe) or "prod" (careful — writes to production!).

        Returns:
            Page ID, title, and URL of the created page.
        """
        err = _check_write_config(instance)
        if err:
            return {"error": err}

        write_cfg = _get_write_config(instance)
        if not write_cfg:
            return {"error": f"Instance '{instance}' not configured"}
        base_url, auth = write_cfg
        headers = {"Authorization": auth, "Accept": "application/json"}

        body: dict = {
            "spaceId": None,
            "status": status,
            "title": title,
            "body": {"representation": "storage", "value": content},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            space_resp = await client.get(
                f"{base_url}/wiki/api/v2/spaces",
                headers=headers,
                params={"keys": space_key, "limit": 1},
            )
            if not space_resp.is_success:
                return {"error": f"Could not find space '{space_key}': {space_resp.status_code}"}
            spaces = space_resp.json().get("results", [])
            if not spaces:
                return {"error": f"Space '{space_key}' not found in {instance} instance"}
            body["spaceId"] = spaces[0]["id"]

            if parent_id:
                body["parentId"] = parent_id

            resp = await client.post(
                f"{base_url}/wiki/api/v2/pages",
                headers={**headers, "Content-Type": "application/json"},
                json=body,
            )

        if resp.status_code == 400:
            return {"error": f"Bad request (invalid Confluence storage format HTML): {resp.text[:500]}"}
        if resp.status_code == 401:
            return {"error": "Authentication failed"}
        if resp.status_code == 403:
            return {"error": "Permission denied — check your Confluence token has write access"}
        if resp.status_code == 409:
            # Page already exists — find it and update instead (upsert behaviour)
            async with httpx.AsyncClient(timeout=30.0) as client2:
                search_resp = await client2.get(
                    f"{base_url}/wiki/rest/api/content",
                    headers=headers,
                    params={"title": title, "spaceKey": space_key, "expand": "version"},
                )
            if search_resp.is_success:
                results = search_resp.json().get("results", [])
                if results:
                    existing = results[0]
                    existing_id = existing["id"]
                    current_version = existing["version"]["number"]
                    async with httpx.AsyncClient(timeout=30.0) as client3:
                        update_resp = await client3.put(
                            f"{base_url}/wiki/api/v2/pages/{existing_id}",
                            headers={**headers, "Content-Type": "application/json"},
                            json={
                                "id": existing_id,
                                "status": status,
                                "title": title,
                                "body": {"representation": "storage", "value": content},
                                "version": {
                                    "number": current_version + 1,
                                    "message": "Updated by CodeMie API Design Generator",
                                },
                            },
                        )
                    if update_resp.is_success:
                        data = update_resp.json()
                        return {
                            "id": data.get("id"),
                            "title": data.get("title"),
                            "status": data.get("status"),
                            "instance": instance,
                            "url": f"{base_url}/wiki" + data.get("_links", {}).get("webui", ""),
                            "version": data.get("version", {}).get("number", current_version + 1),
                            "upserted": True,
                        }
                    return {"error": f"Page existed, update also failed: {update_resp.text[:300]}"}
            return {"error": f"Page with title '{title}' already exists in space '{space_key}' (could not auto-update)"}
        if not resp.is_success:
            return {"error": f"Confluence API error {resp.status_code}: {resp.text[:300]}"}

        data = resp.json()
        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "status": data.get("status"),
            "instance": instance,
            "url": f"{base_url}/wiki" + data.get("_links", {}).get("webui", ""),
            "version": data.get("version", {}).get("number", 1),
        }

    @mcp.tool()
    async def confluence_update_page(
        page_id: str,
        title: str,
        content: str,
        version: int,
        status: str = "current",
        instance: str = "sandbox",
    ) -> dict:
        """Update an existing Confluence page.

        Replaces the page content. You must provide the current version number
        (get it from confluence_get_page). Each update increments version by 1.

        Args:
            page_id: Numeric page ID from the Confluence URL.
            title: Page title (can be same or updated).
            content: New page body in Confluence storage format HTML.
            version: Current version number. Use confluence_get_page to get it.
            status: "current" (published) or "draft".
            instance: "sandbox" (default) or "prod".

        Returns:
            Updated page ID, title, new version number, and URL.
        """
        err = _check_write_config(instance)
        if err:
            return {"error": err}

        write_cfg = _get_write_config(instance)
        if not write_cfg:
            return {"error": f"Instance '{instance}' not configured"}
        base_url, auth = write_cfg
        headers = {"Authorization": auth, "Accept": "application/json"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.put(
                f"{base_url}/wiki/api/v2/pages/{page_id}",
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "id": page_id,
                    "status": status,
                    "title": title,
                    "body": {"representation": "storage", "value": content},
                    "version": {
                        "number": version + 1,
                        "message": "Updated by CodeMie API Design Generator",
                    },
                },
            )

        if resp.status_code == 400:
            return {"error": f"Bad request: {resp.text[:300]}"}
        if resp.status_code == 401:
            return {"error": "Authentication failed"}
        if resp.status_code == 403:
            return {"error": "Permission denied"}
        if resp.status_code == 404:
            return {"error": f"Page '{page_id}' not found"}
        if resp.status_code == 409:
            return {"error": "Version conflict — get current version with confluence_get_page and retry"}
        if not resp.is_success:
            return {"error": f"Confluence API error {resp.status_code}: {resp.text[:300]}"}

        data = resp.json()
        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "status": data.get("status"),
            "instance": instance,
            "version": data.get("version", {}).get("number"),
            "url": f"{base_url}/wiki" + data.get("_links", {}).get("webui", ""),
        }

    @mcp.tool()
    async def confluence_delete_page(page_id: str) -> dict:
        """Delete a Confluence page by ID.

        Permanently deletes the page. Use with caution — this cannot be undone
        unless you restore from the Confluence trash.

        Args:
            page_id: Numeric page ID to delete.

        Returns:
            Success confirmation or error message.
        """
        err = _check_config()
        if err:
            return {"error": err}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.delete(
                f"{_base_url()}/wiki/api/v2/pages/{page_id}",
                headers=_default_headers(),
            )

        if resp.status_code == 204:
            return {"success": True, "message": f"Page {page_id} deleted"}
        if resp.status_code == 404:
            return {"error": f"Page '{page_id}' not found"}
        if resp.status_code == 403:
            return {"error": "Permission denied"}
        return {"error": f"Confluence API error {resp.status_code}: {resp.text[:200]}"}

    @mcp.tool()
    async def confluence_get_author_info() -> dict:
        """Return the configured author details for use in Document History rows.

        Returns the Atlassian account ID (set via MSC_CONFLUENCE_AUTHOR_ACCOUNT_ID)
        and the pre-built Confluence storage format snippets for the author mention
        and the Draft status macro, ready to be inserted directly into page HTML.
        """
        account_id = settings.confluence_author_account_id

        if account_id:
            author_macro = (
                f'<ac:link><ri:user ri:account-id="{account_id}" /></ac:link>'
                ' Co-authored by MSC BA Agent'
            )
        else:
            author_macro = "Sarah Suda, Co-authored by MSC BA Agent"

        status_macro = (
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Blue</ac:parameter>'
            '<ac:parameter ac:name="title">Draft</ac:parameter>'
            '</ac:structured-macro>'
        )

        return {
            "account_id": account_id,
            "author_cell_html": author_macro,
            "status_cell_html": status_macro,
            "note": (
                "account_id is blank — falling back to plain text author name. "
                "Set MSC_CONFLUENCE_AUTHOR_ACCOUNT_ID in .env to enable the @mention macro."
            ) if not account_id else "OK",
        }
