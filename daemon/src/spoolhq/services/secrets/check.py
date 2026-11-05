"""Testing a stored secret with one read-only HTTPS call to its provider.

The answer is one of a few fixed texts: never the secret, a response body or a header.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass

import httpx

from spoolhq.services.secrets import SecretName, read_secret

logger = logging.getLogger(__name__)

TIMEOUT_S = 10.0
ANTHROPIC_VERSION = "2023-06-01"


@dataclass(frozen=True)
class SecretCheck:
    ok: bool
    message: str


# name -> (provider, fixed HTTPS URL, request headers for the secret)
PROBES: dict[SecretName, tuple[str, str, Callable[[str], dict[str, str]]]] = {
    "anthropic": (
        "Anthropic",
        "https://api.anthropic.com/v1/models",
        lambda key: {"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION},
    ),
    "github": (
        "GitHub",
        "https://api.github.com/user",
        lambda token: {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    ),
    "clickup": (
        "ClickUp",
        "https://api.clickup.com/api/v2/user",
        lambda token: {"Authorization": token},
    ),
}


def check_secret(name: SecretName, *, transport: httpx.BaseTransport | None = None) -> SecretCheck:
    result = _check(name, transport)
    logger.info("secret tested", extra={"secret": name, "outcome": result.message})
    return result


def _check(name: SecretName, transport: httpx.BaseTransport | None) -> SecretCheck:
    secret = read_secret(name)
    if secret is None:
        return SecretCheck(False, "Not set")
    provider, url, headers = PROBES[name]
    try:
        with httpx.Client(
            timeout=TIMEOUT_S,
            follow_redirects=False,
            headers={"User-Agent": "spoolhq"},
            transport=transport,
        ) as client:
            status = client.get(url, headers=headers(secret)).status_code
    except httpx.TimeoutException:
        return SecretCheck(False, "Timed out")
    except httpx.HTTPError:
        return SecretCheck(False, f"Couldn't reach {provider}")
    if status == 200:
        return SecretCheck(True, "Key works")
    if status in (401, 403):
        return SecretCheck(False, f"Rejected ({status})")
    return SecretCheck(False, f"Unexpected response ({status})")
