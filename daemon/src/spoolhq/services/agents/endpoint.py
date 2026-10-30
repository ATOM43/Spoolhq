"""The token SpoolHQ gives an agent CLI for a custom endpoint (``base_url``).

With a custom endpoint the CLI must never fall back to the user's own subscription
login, which it would send to that address. So SpoolHQ supplies a credential itself: a
fixed dummy for an endpoint on this machine (local servers such as Ollama ignore it),
otherwise ``SPOOLHQ_ENDPOINT_TOKEN_<BACKEND>`` from the environment or the OS keychain
(``keyring``, service ``spoolhq``, key ``endpoint:<backend>``). See ``docs/agents.md``.
"""

import logging
import os
import re
from urllib.parse import urlsplit

import keyring
from keyring.errors import KeyringError

logger = logging.getLogger(__name__)

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
LOCAL_TOKEN = "spoolhq-local-endpoint"  # noqa: S105 - a public dummy
"""What a local endpoint gets: never a real credential."""
KEYRING_SERVICE = "spoolhq"


def token_var(backend: str) -> str:
    """``SPOOLHQ_ENDPOINT_TOKEN_CLAUDE_CODE_CLI`` for ``claude-code-cli``."""
    return "SPOOLHQ_ENDPOINT_TOKEN_" + re.sub(r"[^A-Z0-9]", "_", backend.upper())


def keyring_key(backend: str) -> str:
    return f"endpoint:{backend}"


def missing_token(backend: str, base_url: str) -> str:
    return (
        f"custom endpoint {base_url} needs its own token; "
        f"run spool secrets set {keyring_key(backend)}"
    )


def endpoint_token(backend: str, base_url: str) -> str | None:
    """The token for ``base_url``; None for a remote endpoint without one."""
    if urlsplit(base_url).hostname in LOCAL_HOSTS:
        return LOCAL_TOKEN
    token = os.environ.get(token_var(backend), "").strip()
    if token:
        return token
    try:
        stored = keyring.get_password(KEYRING_SERVICE, keyring_key(backend))
    except (KeyringError, RuntimeError) as exc:
        logger.warning("cannot read the OS keychain", extra={"error": type(exc).__name__})
        return None
    return (stored or "").strip() or None


def store_endpoint_token(backend: str, token: str) -> None:
    """Save ``token`` in the OS keychain; KeyringError if there is no usable keychain."""
    if not token.strip():
        raise ValueError("the token is empty")
    keyring.set_password(KEYRING_SERVICE, keyring_key(backend), token.strip())
