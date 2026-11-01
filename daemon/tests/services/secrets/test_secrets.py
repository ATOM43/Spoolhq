"""Secret status, storing and removing (the autouse in-memory keychain)."""

import pytest

from spoolhq.services.secrets import delete_secret, secret_status, store_secret
from tests.conftest import MemoryKeyring


def test_environment_wins_over_the_keychain(
    keychain: MemoryKeyring, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert secret_status("anthropic").source is None
    store_secret("anthropic", " sk-x ")
    assert keychain.get_password("spoolhq", "anthropic") == "sk-x"
    assert secret_status("anthropic").source == "keychain"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-env")
    assert secret_status("anthropic").source == "env"
    delete_secret("anthropic")
    delete_secret("anthropic")  # nothing there: no error
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert not secret_status("anthropic").set


def test_empty_values_and_an_unreadable_keychain(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="empty"):
        store_secret("github", "  ")

    def broken(*_args: object) -> None:
        raise RuntimeError("no keychain")

    monkeypatch.setattr("keyring.get_password", broken)
    assert secret_status("clickup").set is False
