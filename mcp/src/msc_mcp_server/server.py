"""MSC MCP Server - entry point.

Supports three transport modes:
  - SSE:             python -m msc_mcp_server.server --transport sse
  - Streamable HTTP: python -m msc_mcp_server.server --transport streamable-http
  - Stdio:           python -m msc_mcp_server.server --transport stdio

The SSE endpoint is at /sse, Streamable HTTP at /mcp.
"""

import argparse
import contextlib
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from mcp.server.fastmcp import FastMCP

from msc_mcp_server.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Shared application context available to all tools via lifespan."""

    http_clients: dict = field(default_factory=dict)


@contextlib.asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Initialize shared resources on startup, clean up on shutdown."""
    import httpx

    ctx = AppContext()
    # Pre-create httpx clients for downstream APIs (reused across tool calls)
    ctx.http_clients["default"] = httpx.AsyncClient(timeout=30.0)
    logger.info("MSC MCP Server started — transport: %s", settings.transport)
    try:
        yield ctx
    finally:
        for client in ctx.http_clients.values():
            await client.aclose()
        logger.info("MSC MCP Server stopped")


def create_server(host: str | None = None, port: int | None = None) -> FastMCP:
    """Build and return the FastMCP server instance with all tools registered."""
    mcp = FastMCP(
        settings.server_name,
        host=host or settings.host,
        port=port or settings.port,
        stateless_http=True,
        json_response=True,
        lifespan=app_lifespan,
    )

    # Import tool modules — each module registers its tools on the mcp instance
    from msc_mcp_server.tools.registry import register_all_tools

    register_all_tools(mcp)

    # Import resources and prompts
    from msc_mcp_server.prompts.templates import register_prompts
    from msc_mcp_server.resources.project_info import register_resources

    register_resources(mcp)
    register_prompts(mcp)

    return mcp


# Module-level instance for `mcp dev` inspector and direct imports
mcp = create_server()


def run_with_auth(mcp_server: FastMCP, transport: str, host: str, port: int):
    """Run the MCP server with Bearer token auth middleware for HTTP transports."""
    if transport == "stdio" or not settings.api_token:
        # stdio doesn't use HTTP; no token configured = open access
        mcp_server.run(transport=transport)
        return

    import uvicorn

    from msc_mcp_server.auth import BearerTokenMiddleware

    # Get the ASGI app from FastMCP (includes its own lifespan for session management)
    if transport == "streamable-http":
        inner_app = mcp_server.streamable_http_app()
    else:  # sse
        inner_app = mcp_server.sse_app()

    # Wrap with pure ASGI auth middleware (doesn't buffer streaming responses)
    app = BearerTokenMiddleware(inner_app)

    logger.info("Auth enabled — Bearer token required")
    uvicorn.run(app, host=host, port=port)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="MSC MCP Server")
    parser.add_argument(
        "--transport",
        choices=["sse", "streamable-http", "stdio"],
        default=settings.transport,
        help="Transport mode (default: %(default)s)",
    )
    parser.add_argument("--host", default=settings.host, help="Host to bind (default: %(default)s)")
    parser.add_argument("--port", type=int, default=settings.port, help="Port to bind (default: %(default)s)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    mcp_server = create_server(host=args.host, port=args.port)

    logger.info("Starting MSC MCP Server on %s:%s (transport=%s)", args.host, args.port, args.transport)
    run_with_auth(mcp_server, args.transport, args.host, args.port)


if __name__ == "__main__":
    main()
