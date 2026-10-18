"""Request checks that keep the API local: the Host header and the bearer token."""

import logging
import secrets

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)

PUBLIC_ROUTES = frozenset({("GET", "/api/health")})


def _is_api_path(path: str) -> bool:
    return path == "/api" or path.startswith("/api/")


class LocalOnlyMiddleware:
    """Reject requests with a foreign Host header (400) and API calls without the token (401).

    The Host check blocks DNS rebinding: a web page whose domain resolves to 127.0.0.1
    still sends its own domain in Host. Every ``/api/*`` route needs the token unless it
    is listed in PUBLIC_ROUTES, so new routes are protected by default.
    """

    def __init__(self, app: ASGIApp, *, port: int, token: str) -> None:
        self.app = app
        self._allowed_hosts = frozenset(
            {f"127.0.0.1:{port}".encode(), f"localhost:{port}".encode()}
        )
        self._token = token.encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        path: str = scope["path"]
        host = headers.get(b"host", b"").lower()
        if host not in self._allowed_hosts:
            logger.warning(
                "rejected request with unexpected Host header",
                extra={"host": host.decode("latin-1"), "path": path},
            )
            await self._reject(scope, receive, send, 400, "invalid Host header")
            return

        method = scope.get("method", "GET")
        if _is_api_path(path) and (method, path) not in PUBLIC_ROUTES:
            scheme, _, provided = headers.get(b"authorization", b"").partition(b" ")
            valid = scheme.lower() == b"bearer" and secrets.compare_digest(provided, self._token)
            if not valid:
                logger.info("rejected unauthenticated request", extra={"path": path})
                await self._reject(scope, receive, send, 401, "missing or invalid token")
                return

        await self.app(scope, receive, send)

    async def _reject(
        self, scope: Scope, receive: Receive, send: Send, status: int, detail: str
    ) -> None:
        if scope["type"] == "websocket":
            # Closing before accept makes the server answer the handshake with 403.
            await send({"type": "websocket.close", "code": 1008})
            return
        headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
        response = JSONResponse({"detail": detail}, status_code=status, headers=headers)
        await response(scope, receive, send)
