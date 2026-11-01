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


def secret_status(name: SecretName) -> SecretStatus:
    env_var, key = SECRETS[name]
    if os.environ.get(env_var, "").strip():
        return SecretStatus(True, "env")
    try:
        stored = keyring.get_password(KEYRING_SERVICE, key)
    except (KeyringError, RuntimeError) as exc:
        logger.warning("cannot read the OS keychain", extra={"error": type(exc).__name__})
        return SecretStatus(False, None)
    return SecretStatus(True, "keychain") if (stored or "").strip() else SecretStatus(False, None)


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
