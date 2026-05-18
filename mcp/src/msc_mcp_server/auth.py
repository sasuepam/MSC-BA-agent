"""Bearer token authentication middleware for the MCP server.

Uses a pure ASGI middleware (not BaseHTTPMiddleware) to avoid
breaking streaming responses required by MCP's streamable-http transport.

Accepts the token via:
  - Authorization: Bearer <token>  header  (standard clients)
  - ?token=<token>                 query param  (Codemie / URL-only clients)
"""

import json
import logging
from urllib.parse import parse_qs

from msc_mcp_server.config import settings

logger = logging.getLogger(__name__)


class BearerTokenMiddleware:
    """Pure ASGI middleware that rejects requests without a valid token.

    Token can be supplied as an Authorization: Bearer header or as a
    ?token= query parameter (useful for clients like Codemie that only
    accept a URL in their MCP config).

    If MSC_API_TOKEN is empty, auth is disabled (open access).
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Only check HTTP requests (pass through lifespan, websocket, etc.)
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Skip auth if no token configured
        if not settings.api_token:
            await self.app(scope, receive, send)
            return

        token = self._extract_token(scope)
        if token is None:
            logger.warning("Rejected request: no token provided")
            await self._send_json(send, 401, {"error": "Missing token — use Authorization: Bearer header or ?token= param"})
            return

        if token != settings.api_token:
            logger.warning("Rejected request: invalid token")
            await self._send_json(send, 403, {"error": "Invalid token"})
            return

        await self.app(scope, receive, send)

    @staticmethod
    def _extract_token(scope) -> str | None:
        """Return the token from Authorization header or ?token= query param, or None."""
        # 1. Check Authorization: Bearer header
        headers = dict(scope.get("headers", []))
        auth_value = headers.get(b"authorization", b"").decode()
        if auth_value.startswith("Bearer "):
            return auth_value.removeprefix("Bearer ").strip()

        # 2. Fall back to ?token= query parameter
        qs = scope.get("query_string", b"").decode()
        params = parse_qs(qs)
        token_list = params.get("token")
        if token_list:
            return token_list[0]

        return None

    @staticmethod
    async def _send_json(send, status: int, body: dict):
        """Send a JSON error response via raw ASGI."""
        payload = json.dumps(body).encode()
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(payload)).encode()],
            ],
        })
        await send({"type": "http.response.body", "body": payload})
