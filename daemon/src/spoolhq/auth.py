"""The local bearer token shared by the daemon and its clients."""

import os
import secrets
import stat
import sys
from pathlib import Path


def token_path(home: Path) -> Path:
    return home / "token"


def read_token(home: Path) -> str | None:
    """Return the saved token, or None if there is none yet."""
    try:
        token = token_path(home).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    return token or None


def load_or_create_token(home: Path) -> str:
    """Return the saved token, creating it (mode 0600 on POSIX) on first use."""
    path = token_path(home)
    existing = read_token(home)
    if existing is not None:
        if sys.platform != "win32" and stat.S_IMODE(path.stat().st_mode) & 0o077:
            path.chmod(0o600)
        return existing

    token = secrets.token_urlsafe(32)
    # The mode applies when the file is created; fchmod also fixes an empty file left
    # behind by an interrupted write. On Windows the mode is best effort.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        if sys.platform != "win32":
            os.fchmod(file.fileno(), 0o600)
        file.write(token)
    return token
