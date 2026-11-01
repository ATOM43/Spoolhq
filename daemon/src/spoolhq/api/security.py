"""Request checks that keep the API local: the Host header, the bearer token and the
request body size."""

import logging
import re
import secrets

from fastapi.security import HTTPBearer
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from spoolhq.api.errors import error_response

logger = logging.getLogger(__name__)

PUBLIC_ROUTES = frozenset({("GET", "/api/health")})
# WebSockets that check the token themselves, in their first message (a browser can't
# set headers on a WebSocket, and a token in the query string ends up in logs).
MESSAGE_AUTH_SOCKETS = re.compile(r"/api/projects/[^/]+/events")
MAX_BODY_BYTES = 1024 * 1024

# LocalOnlyMiddleware enforces the token; routers depend on this only to document it in
# /docs, where the Authorize button then works.
bearer_scheme = HTTPBearer(auto_error=False, description="The token in ~/.spoolhq/token")


def _is_api_path(path: str) -> bool:
    return path == "/api" or path.startswith("/api/")


class LocalOnlyMiddleware:
    """Reject requests with a foreign Host header (400), API calls without the token (401)
    and request bodies over 1 MB (413).

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
        socket_auth = scope["type"] == "websocket" and MESSAGE_AUTH_SOCKETS.fullmatch(path)
        if _is_api_path(path) and (method, path) not in PUBLIC_ROUTES and not socket_auth:
            scheme, _, provided = headers.get(b"authorization", b"").partition(b" ")
            valid = scheme.lower() == b"bearer" and secrets.compare_digest(provided, self._token)
            if not valid:
                logger.info("rejected unauthenticated request", extra={"path": path})
                await self._reject(scope, receive, send, 401, "missing or invalid token")
                return

        if scope["type"] == "http":
            body = await _read_body(receive)
            if body is None:
                await self._reject(scope, receive, send, 413, "the request body is over 1 MB")
                return
            receive = _replay(body, receive)
        await self.app(scope, receive, send)

    async def _reject(
        self, scope: Scope, receive: Receive, send: Send, status: int, detail: str
    ) -> None:
        if scope["type"] == "websocket":
            # Closing before accept makes the server answer the handshake with 403.
            await send({"type": "websocket.close", "code": 1008})
            return
        headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
        codes = {400: "bad_host", 401: "unauthorized", 413: "payload_too_large"}
        await error_response(status, codes[status], detail, headers)(scope, receive, send)


async def _read_body(receive: Receive) -> bytes | None:
    """The whole request body, or None once it passes MAX_BODY_BYTES."""
    chunks: list[bytes] = []
    size = 0
    while True:
        message = await receive()
        if message["type"] != "http.request":
            return b"".join(chunks)
        chunk = message.get("body", b"")
        size += len(chunk)
        if size > MAX_BODY_BYTES:
            return None
        chunks.append(chunk)
        if not message.get("more_body", False):
            return b"".join(chunks)


def _replay(body: bytes, receive: Receive) -> Receive:
    """The body once, then the real messages (a streaming response waits for disconnect)."""
    sent = False

    async def replay() -> Message:
        nonlocal sent
        if sent:
            return await receive()
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return replay
