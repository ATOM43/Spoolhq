"""The GitHub REST API client: the token, headers, timeouts, rate limits and redaction.

The token goes only into the ``Authorization`` header; every error message passes
through ``redact`` first, so it can't reach a log, a run file or the API's answers.
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, Self

import httpx

API_URL = "https://api.github.com"
API_VERSION = "2022-11-28"
TIMEOUT_S = 30.0
DEFAULT_RETRY_S = 60
REDACTED = "[redacted]"
MESSAGE_MAX = 300


class GitHubError(Exception):
    """A GitHub API call failed. ``status`` is the HTTP status (None if there was no
    answer); ``retry_at`` is set when GitHub asked to wait (a rate limit)."""

    def __init__(
        self, message: str, *, status: int | None = None, retry_at: datetime | None = None
    ) -> None:
        super().__init__(message)
        self.status = status
        self.retry_at = retry_at


class GitHubClient:
    def __init__(
        self,
        token: str,
        *,
        transport: httpx.BaseTransport | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._token = token
        self._clock = clock
        self._http = httpx.Client(
            base_url=API_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "spoolhq",
            },
            timeout=TIMEOUT_S,
            transport=transport,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def redact(self, text: str) -> str:
        return text.replace(self._token, REDACTED) if self._token else text

    def request(
        self, method: str, path: str, *, json: Any = None, params: dict[str, Any] | None = None
    ) -> Any:
        """The decoded JSON answer (None for an empty one); GitHubError otherwise."""
        what = f"GitHub API {method} {path}"
        try:
            response = self._http.request(method, path, json=json, params=params)
        except httpx.HTTPError as exc:
            # `from None`: the httpx exception holds the request, headers included.
            raise GitHubError(self.redact(f"{what}: {type(exc).__name__}: {exc}")) from None
        status = response.status_code
        retry_at = self._retry_at(response)
        if retry_at is not None:
            raise GitHubError(
                f"{what}: rate limited (HTTP {status}); retry after {retry_at:%H:%M:%S} UTC",
                status=status,
                retry_at=retry_at,
            )
        if response.is_error:
            message = self.redact(_message(response))[:MESSAGE_MAX]
            raise GitHubError(f"{what}: HTTP {status}: {message}", status=status)
        return response.json() if response.content else None

    def _retry_at(self, response: httpx.Response) -> datetime | None:
        """When to try again after a rate limit (``Retry-After`` or the reset time of an
        exhausted ``X-RateLimit-Remaining``); None if this isn't one."""
        if response.status_code not in (403, 429):
            return None
        headers = response.headers
        if (after := headers.get("Retry-After", "")).isdigit():
            return self._clock() + timedelta(seconds=int(after))
        if headers.get("X-RateLimit-Remaining") == "0":
            reset = headers.get("X-RateLimit-Reset", "")
            if reset.isdigit():
                return datetime.fromtimestamp(int(reset), UTC)
            return self._clock() + timedelta(seconds=DEFAULT_RETRY_S)
        if response.status_code == 429:
            return self._clock() + timedelta(seconds=DEFAULT_RETRY_S)
        return None


def _message(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text.strip() or response.reason_phrase
    if isinstance(data, dict) and isinstance(data.get("message"), str):
        errors = data.get("errors")
        detail = f" ({errors})" if errors else ""
        return f"{data['message']}{detail}"
    return response.reason_phrase
