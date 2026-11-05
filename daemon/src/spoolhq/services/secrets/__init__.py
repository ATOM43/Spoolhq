"""Secrets: whether each of SpoolHQ's secrets is set and where, and storing or removing
one in the OS keychain (``keyring``, service ``spoolhq``). The environment variable wins
over the keychain, as in the code that uses each secret. Values are never returned,
logged or written to a file."""

import logging
import os
from dataclasses import dataclass
from typing import Literal

import keyring
from keyring.errors import KeyringError, PasswordDeleteError

from spoolhq.services.agents import agent_sdk, claude_config
from spoolhq.services.github import token as github

logger = logging.getLogger(__name__)

SecretName = Literal["anthropic", "github", "clickup"]
SecretSource = Literal["keychain", "env"]
KEYRING_SERVICE = "spoolhq"
# name -> (environment variable, keychain key)
SECRETS: dict[SecretName, tuple[str, str]] = {
    "anthropic": (claude_config.API_KEY_VAR, agent_sdk.KEYRING_KEY),
    "github": (github.ENV_VAR, github.KEYRING_KEY),
    "clickup": ("SPOOLHQ_CLICKUP_TOKEN", "clickup"),
}


@dataclass(frozen=True)
class SecretStatus:
    set: bool
    source: SecretSource | None


def _lookup(name: SecretName) -> tuple[str, SecretSource] | None:
    env_var, key = SECRETS[name]
    from_env = os.environ.get(env_var, "").strip()
    if from_env:
        return from_env, "env"
    try:
        stored = (keyring.get_password(KEYRING_SERVICE, key) or "").strip()
    except (KeyringError, RuntimeError) as exc:
        logger.warning("cannot read the OS keychain", extra={"error": type(exc).__name__})
        return None
    return (stored, "keychain") if stored else None


def secret_status(name: SecretName) -> SecretStatus:
    found = _lookup(name)
    return SecretStatus(True, found[1]) if found else SecretStatus(False, None)


def read_secret(name: SecretName) -> str | None:
    """The value the daemon would use (env first), for the daemon's own calls only."""
    found = _lookup(name)
    return found[0] if found else None


def store_secret(name: SecretName, value: str) -> None:
    """Save ``value`` in the keychain; ValueError if empty, KeyringError without a keychain."""
    if not value.strip():
        raise ValueError(f"the {name} secret is empty")
    keyring.set_password(KEYRING_SERVICE, SECRETS[name][1], value.strip())


def delete_secret(name: SecretName) -> None:
    """Remove it from the keychain; nothing happens if it isn't there."""
    try:
        keyring.delete_password(KEYRING_SERVICE, SECRETS[name][1])
    except PasswordDeleteError:
        return
