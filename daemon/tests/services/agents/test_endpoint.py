"""The token SpoolHQ supplies for a custom endpoint, so no subscription login reaches it."""

import pytest
from keyring.errors import KeyringError

from spoolhq.services.agents import endpoint
from spoolhq.services.agents.endpoint import (
    LOCAL_TOKEN,
    endpoint_token,
    missing_token,
    store_endpoint_token,
    token_var,
)
from tests.conftest import MemoryKeyring

REMOTE = "https://llm.example.com"


def test_names() -> None:
    assert token_var("claude-code-cli") == "SPOOLHQ_ENDPOINT_TOKEN_CLAUDE_CODE_CLI"
    assert token_var("codex-cli") == "SPOOLHQ_ENDPOINT_TOKEN_CODEX_CLI"
    assert missing_token("codex-cli", REMOTE) == (
        "custom endpoint https://llm.example.com needs its own token; "
        "run spool secrets set endpoint:codex-cli"
    )


@pytest.mark.parametrize(
    "url", ["http://localhost:11434", "http://127.0.0.1:8080/v1", "http://[::1]:11434"]
)
def test_a_local_endpoint_gets_the_dummy(
    url: str, keychain: MemoryKeyring, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SPOOLHQ_ENDPOINT_TOKEN_CODEX_CLI", "real")
    keychain.passwords[("spoolhq", "endpoint:codex-cli")] = "stored"
    assert endpoint_token("codex-cli", url) == LOCAL_TOKEN


def test_a_remote_endpoint_uses_the_environment_then_the_keychain(
    keychain: MemoryKeyring, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert endpoint_token("codex-cli", REMOTE) is None
    keychain.passwords[("spoolhq", "endpoint:codex-cli")] = " stored \n"
    assert endpoint_token("codex-cli", REMOTE) == "stored"
    monkeypatch.setenv("SPOOLHQ_ENDPOINT_TOKEN_CODEX_CLI", "from-env")
    assert endpoint_token("codex-cli", REMOTE) == "from-env"
    assert endpoint_token("claude-code-cli", REMOTE) is None  # per backend


def test_an_unreadable_keychain_means_no_token(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(service: str, key: str) -> str:
        raise KeyringError("locked")

    monkeypatch.setattr(endpoint.keyring, "get_password", broken)
    assert endpoint_token("codex-cli", REMOTE) is None


def test_store(keychain: MemoryKeyring) -> None:
    store_endpoint_token("codex-cli", " tok\n")
    assert keychain.passwords == {("spoolhq", "endpoint:codex-cli"): "tok"}
    with pytest.raises(ValueError, match="empty"):
        store_endpoint_token("codex-cli", "  ")
