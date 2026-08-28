"""MCP Resources — read-only context data that agents can reference."""

import json

from mcp.server.fastmcp import FastMCP

from msc_mcp_server import __version__
from msc_mcp_server.config import settings


def register_resources(mcp: FastMCP) -> None:
    """Register resource endpoints on the MCP server."""

    @mcp.resource("config://server")
    def server_config() -> str:
        """Current server configuration (non-sensitive)."""
        return json.dumps(
            {
                "server_name": settings.server_name,
                "version": __version__,
                "transport": settings.transport,
                "host": settings.host,
                "port": settings.port,
            },
            indent=2,
        )

    @mcp.resource("config://integrations")
    def integration_status() -> str:
        """Which downstream integrations are configured."""
        return json.dumps(
            {
                "jira": {
                    "configured": bool(settings.jira_url and settings.jira_token),
                    "url": settings.jira_url or None,
                },
                "confluence": {
                    "configured": bool(settings.confluence_url and settings.confluence_token),
                    "url": settings.confluence_url or None,
                },
                "anypoint": {"configured": bool(settings.anypoint_client_id), "url": settings.anypoint_url},
                "git": {"configured": bool(settings.git_token), "provider": settings.git_provider or None},
                "office365": {"configured": bool(settings.ms_client_id)},
            },
            indent=2,
        )
