"""Agent settings a repo can carry: files that change an agent's permissions, hooks or tools.

Every backend is started so that it ignores these (see ``docs/agents.md#repo-safety``).
A backend that would still load one lists it in ``unexcluded_settings`` (fnmatch
patterns, relative to the worktree), and ``refusal`` then stops the run before the
agent starts. ``is_settings_path`` marks the files an implementer may not write.
"""

from collections.abc import Iterable
from fnmatch import fnmatchcase
from pathlib import Path

SETTINGS_DIRS = (".claude", ".codex")
SETTINGS_FILES = (".mcp.json",)


def is_settings_path(path: str) -> bool:
    """Whether ``path`` (relative, ``/``-separated, as git prints it) is agent settings:
    anything in a ``.claude/`` or ``.codex/`` folder at any depth, or a ``.mcp.json``."""
    parts = path.split("/")
    return any(part in SETTINGS_DIRS for part in parts[:-1]) or parts[-1] in SETTINGS_FILES


def settings_files(root: Path) -> list[str]:
    """The agent settings files at the top of ``root``, as sorted relative paths."""
    found = [name for name in SETTINGS_FILES if (root / name).is_file()]
    for folder in SETTINGS_DIRS:
        base = root / folder
        if base.is_dir() and not base.is_symlink():
            found += [p.relative_to(root).as_posix() for p in base.rglob("*") if p.is_file()]
        elif base.is_file() or base.is_symlink():
            found.append(folder)
    return sorted(found)


def refusal(runner: object, worktree: Path) -> str | None:
    """Why ``runner`` can't run in ``worktree``: the first settings file it would load.

    The real backends exclude every file (``unexcluded_settings`` empty or absent).
    """
    patterns: tuple[str, ...] = tuple(getattr(runner, "unexcluded_settings", ()))
    backend = getattr(runner, "name", "this backend")
    if not patterns:
        return None
    for path in settings_files(worktree):
        if any(fnmatchcase(path, pattern) for pattern in patterns):
            return f"This repo has agent settings SpoolHQ can't override for {backend}: {path}"
    return None


def changed_settings(paths: Iterable[str]) -> list[str]:
    """The agent settings files among ``paths``."""
    return sorted({path for path in paths if is_settings_path(path)})
