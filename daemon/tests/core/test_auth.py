import stat
import sys
from pathlib import Path

import pytest

from spoolhq.core.auth import load_or_create_token, read_token, token_path
from spoolhq.core.config import ensure_home


def test_token_is_created_once_and_reused(home: Path) -> None:
    first = load_or_create_token(ensure_home())
    assert len(first) >= 43  # token_urlsafe(32)
    assert token_path(home).read_text(encoding="utf-8") == first
    assert load_or_create_token(ensure_home()) == first
    assert read_token(home) == first


def test_empty_token_file_is_replaced(home: Path) -> None:
    ensure_home()
    token_path(home).write_text("", encoding="utf-8")
    assert read_token(home) is None
    token = load_or_create_token(home)
    assert token
    assert read_token(home) == token


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_token_file_and_home_have_private_modes(home: Path) -> None:
    load_or_create_token(ensure_home())
    assert stat.S_IMODE(home.stat().st_mode) == 0o700
    assert stat.S_IMODE(token_path(home).stat().st_mode) == 0o600


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_loose_token_file_mode_is_tightened(home: Path) -> None:
    token = load_or_create_token(ensure_home())
    token_path(home).chmod(0o644)
    assert load_or_create_token(home) == token
    assert stat.S_IMODE(token_path(home).stat().st_mode) == 0o600
