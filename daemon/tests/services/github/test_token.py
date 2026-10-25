"""services/github/token.py: the environment wins over the OS keychain."""

import keyring
import pytest
from keyring.errors import KeyringLocked

from spoolhq.services.github import github_token, store_github_token
from tests.conftest import MemoryKeyring


def test_no_token(keychain: MemoryKeyring) -> None:
    assert github_token() is None


def test_the_keychain(keychain: MemoryKeyring) -> None:
    store_github_token("  from-keychain\n")
    assert keychain.passwords == {("spoolhq", "github"): "from-keychain"}
    assert github_token() == "from-keychain"


def test_the_environment_wins(keychain: MemoryKeyring, monkeypatch: pytest.MonkeyPatch) -> None:
    store_github_token("from-keychain")
    monkeypatch.setenv("SPOOLHQ_GITHUB_TOKEN", "from-env")
    assert github_token() == "from-env"
    monkeypatch.setenv("SPOOLHQ_GITHUB_TOKEN", "  ")
    assert github_token() == "from-keychain"


def test_an_empty_token_is_refused(keychain: MemoryKeyring) -> None:
    with pytest.raises(ValueError, match="the token is empty"):
        store_github_token(" ")
    assert keychain.passwords == {}


def test_an_unreadable_keychain_is_no_token(monkeypatch: pytest.MonkeyPatch) -> None:
    def locked(service: str, key: str) -> str:
        raise KeyringLocked("locked")

    monkeypatch.setattr(keyring, "get_password", locked)
    assert github_token() is None
