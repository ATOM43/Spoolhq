"""A small HTTP client for the local daemon."""

from typing import Any, Self

import httpx

from spoolhq.core.auth import read_token, token_path
from spoolhq.core.config import Settings, home_dir


class ApiError(Exception):
    """The daemon could not be reached or answered with an error."""


class DaemonNotRunning(ApiError):
    """Nothing is listening on the daemon's port."""


class ApiClient:
    def __init__(
        self,
        base_url: str,
        token: str | None,
        *,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        # trust_env=False: the daemon is local, so HTTP(S)_PROXY must not apply.
        self._http = httpx.Client(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
            transport=transport,
            trust_env=False,
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> Self:
        """Connect to the port in settings with the token from the home folder."""
        return cls(f"http://{settings.host}:{settings.port}", read_token(home_dir()))

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def get(self, path: str) -> Any:
        try:
            response = self._http.get(path)
        except httpx.ConnectError as exc:
            raise DaemonNotRunning(f"daemon not running at {self._http.base_url}") from exc
        except httpx.TimeoutException as exc:
            raise ApiError(f"daemon at {self._http.base_url} did not respond") from exc
        except httpx.HTTPError as exc:
            raise ApiError(f"request to daemon failed: {exc}") from exc
        if response.status_code == 401:
            raise ApiError(f"daemon rejected the token in {token_path(home_dir())}")
        if response.is_error:
            raise ApiError(f"daemon returned HTTP {response.status_code} for {path}")
        return response.json()

    def version(self) -> str:
        try:
            return str(self.get("/api/version")["version"])
        except (ValueError, KeyError) as exc:
            # Something else answers on the port: HTML, or JSON without a version.
            base_url = str(self._http.base_url).rstrip("/")
            raise ApiError(f"not a SpoolHQ daemon at {base_url}") from exc
