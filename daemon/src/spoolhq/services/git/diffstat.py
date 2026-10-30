"""What a staged squash changes: each path with its added and removed lines.

Plain values for the merge policy (``services/runloop/policy.py``), read with
``git diff --cached --numstat -z --find-renames``, which names both sides of a rename.
"""

from dataclasses import dataclass
from pathlib import Path

from spoolhq.services.git.runner import run_git


@dataclass(frozen=True)
class ChangedFile:
    path: str
    """Repo-relative POSIX path (the new name of a renamed file)."""
    old_path: str | None
    """The old name of a renamed file; ``None`` otherwise."""
    added: int
    removed: int
    """Line counts; both 0 for a binary file."""


def parse_numstat(out: str) -> list[ChangedFile]:
    """Parse ``--numstat -z``: ``<added>\\t<removed>\\t<path>\\0``, or for a rename
    ``<added>\\t<removed>\\t\\0<old>\\0<new>\\0``; ``-`` counts mark a binary file."""
    fields = out.split("\0")
    changed: list[ChangedFile] = []
    i = 0
    while i < len(fields) and fields[i]:
        added, removed, path = fields[i].split("\t", 2)
        old = None
        if not path:  # a rename: the old and new names follow
            old, path = fields[i + 1], fields[i + 2]
            i += 2
        i += 1
        changed.append(
            ChangedFile(
                path=path,
                old_path=old,
                added=0 if added == "-" else int(added),
                removed=0 if removed == "-" else int(removed),
            )
        )
    return changed


def staged_changes(worktree: Path, base: str) -> list[ChangedFile]:
    """Each file the index of ``worktree`` changes against ``base``."""
    out = run_git(
        ["diff", "--cached", "--numstat", "-z", "--find-renames", "--no-ext-diff", base],
        worktree,
    ).check()
    return parse_numstat(out.stdout)
