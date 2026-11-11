"""Edits of workspace files guarded by an ETag: the quoted SHA-256 of the file's bytes.

``write_if_match`` reads the file, compares its ETag with the one the client last saw and
only then writes (each writer writes a temp file in the same folder and ``os.replace``s
it), all under the project's edit lock, so two API edits can't both win. An external
editor or the CLI doesn't take that lock: one writing between the compare and the
replace is overwritten. See ``docs/api.md``.
"""

import hashlib
import threading
from collections.abc import Callable
from pathlib import Path

from spoolhq.services.projects.errors import ProjectError

_locks: dict[Path, threading.Lock] = {}
_locks_guard = threading.Lock()


class EditConflict(ProjectError):
    """The file changed since the client read it; it is left as it is."""

    def __init__(self, etag: str, data: bytes) -> None:
        super().__init__("the file changed since you loaded it; reload and edit again")
        self.etag = etag
        self.data = data


def etag_of(data: bytes) -> str:
    return f'"{hashlib.sha256(data).hexdigest()}"'


def read_with_etag(path: Path) -> tuple[bytes, str]:
    data = path.read_bytes()
    return data, etag_of(data)


def edit_lock(workspace: Path) -> threading.Lock:
    """The project's edit lock: every API write to a workspace file holds it."""
    with _locks_guard:
        return _locks.setdefault(workspace.resolve(), threading.Lock())


def write_if_match(workspace: Path, path: Path, if_match: str, write: Callable[[], object]) -> str:
    """Call ``write`` only if ``path``'s ETag is ``if_match``; returns the new ETag.

    Raises EditConflict (with the current ETag and bytes) when it differs.
    """
    with edit_lock(workspace):
        data, current = read_with_etag(path)
        if if_match.strip() != current:
            raise EditConflict(current, data)
        write()
        return read_with_etag(path)[1]
