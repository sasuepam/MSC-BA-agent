"""Demo tools — used to validate the MCP server is working end-to-end."""

import platform
from datetime import UTC, datetime

from mcp.server.fastmcp import FastMCP

from msc_mcp_server import __version__
from msc_mcp_server.config import settings


def register(mcp: FastMCP) -> None:
    """Register demo tools on the MCP server instance."""

    @mcp.tool()
    def hello_world(name: str = "Codemie") -> str:
        """Hello World test tool. Call this to verify the MCP connection is working. Optionally pass a name."""
        timestamp = datetime.now(UTC).strftime("%H:%M:%S UTC")
        return f"Hello {name}! MSC BA MCP Server v{__version__} is connected and running at {timestamp}."

    @mcp.tool()
    def echo(message: str) -> str:
        """Echo back the provided message. Use this to test connectivity."""
        return f"[MSC BA MCP] {message}"

    @mcp.tool()
    def health_check() -> dict:
        """Check server health and return status information."""
        return {
            "status": "healthy",
            "server": settings.server_name,
            "version": __version__,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    @mcp.tool()
    def server_info() -> dict:
        """Get detailed server information including configured integrations."""
        integrations = {
            "jira": bool(settings.jira_url and settings.jira_token),
            "confluence": bool(settings.confluence_url and settings.confluence_token),
            "anypoint": bool(settings.anypoint_client_id and settings.anypoint_client_secret),
            "git": bool(settings.git_token),
            "office365": bool(settings.ms_client_id and settings.ms_client_secret),
        }
        return {
            "server_name": settings.server_name,
            "version": __version__,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "transport": settings.transport,
            "integrations": integrations,
            "active_integrations": [k for k, v in integrations.items() if v],
        }

    @mcp.tool()
    def list_available_tools() -> dict:
        """List all available tools on this MCP server with their descriptions."""
        from msc_mcp_server.tools.registry import TOOL_MODULES

        tools = mcp._tool_manager.list_tools()
        return {
            "tools": [{"name": t.name, "description": t.description} for t in tools],
            "total_tools": len(tools),
            "modules": TOOL_MODULES,
        }
