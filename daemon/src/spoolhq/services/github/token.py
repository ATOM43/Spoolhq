"""The GitHub token: ``SPOOLHQ_GITHUB_TOKEN`` from the environment wins, else the OS
keychain (``keyring``, service ``spoolhq``, key ``github``). It is never written
anywhere else."""

import logging
import os

import keyring
from keyring.errors import KeyringError

logger = logging.getLogger(__name__)

ENV_VAR = "SPOOLHQ_GITHUB_TOKEN"
KEYRING_SERVICE = "spoolhq"
KEYRING_KEY = "github"
MISSING = "PR mode needs a GitHub token; run spool secrets set github or set SPOOLHQ_GITHUB_TOKEN"


def github_token() -> str | None:
    """The token, or None if there is none (or the keychain can't be read)."""
    token = os.environ.get(ENV_VAR, "").strip()
    if token:
        return token
    try:
        stored = keyring.get_password(KEYRING_SERVICE, KEYRING_KEY)
    except (KeyringError, RuntimeError) as exc:
        logger.warning("cannot read the OS keychain", extra={"error": type(exc).__name__})
        return None
    return (stored or "").strip() or None


def store_github_token(token: str) -> None:
    """Save ``token`` in the OS keychain; KeyringError if there is no usable keychain."""
    if not token.strip():
        raise ValueError("the token is empty")
    keyring.set_password(KEYRING_SERVICE, KEYRING_KEY, token.strip())
