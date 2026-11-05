"""Reading the repository's notes, with ``DECISIONS.md`` as a full log or as an index.

A full log (the usual layout) is returned as it is; the renderer keeps its newest lines.
An index (``NNN · title · docs/decisions/<area>.md`` lines, SpoolHQ's own layout) is
expanded: the newest ``count`` numbers are loaded in full from their area files, in
number order. The repository is untrusted, so an area path is read only when it is
relative, has no ``..``, and resolves (symlinks followed) to a file inside the repo.
A decision that can't be loaded keeps its index line, and one warning is logged.
"""

import logging
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

from spoolhq.services.context.model import RepoDocs

logger = logging.getLogger(__name__)

_INDEX_LINE = re.compile(r"(\d+) · (.*) · ([^·]+\.md)")
_ENTRY_START = re.compile(r"(\d+)\. ")


def read_repo_docs(repo: Path, decisions_count: int) -> RepoDocs:
    """``CLAUDE.md``, ``PROGRESS.md`` and ``DECISIONS.md`` from ``repo`` (``None`` if missing)."""
    decisions = _read(repo / "DECISIONS.md")
    expanded = expand_index(repo, decisions, decisions_count) if decisions else None
    return RepoDocs(
        claude_md=_read(repo / "CLAUDE.md"),
        progress_md=_read(repo / "PROGRESS.md"),
        decisions_md=expanded if expanded is not None else decisions,
        decisions_selected=expanded is not None,
    )


def expand_index(repo: Path, text: str, count: int) -> str | None:
    """The newest ``count`` decisions in full, or ``None`` if ``text`` is not an index."""
    index = sorted(
        (int(match[1]), line, match[3])
        for line in text.splitlines()
        if (match := _INDEX_LINE.fullmatch(line.strip()))
    )
    if not index:
        return None
    files: dict[str, dict[int, str] | None] = {}
    entries: list[str] = []
    missing: list[str] = []
    for number, line, rel in index[-count:]:
        if rel not in files:
            files[rel] = _area_entries(repo, rel)
        area = files[rel]
        entry = area.get(number) if area is not None else None
        if entry is None:
            missing.append(f"{number} ({rel})")
        entries.append(entry if entry is not None else line.strip())
    if missing:
        logger.warning(
            "DECISIONS.md: kept the index line for decisions whose entry couldn't be read: %s",
            ", ".join(missing),
        )
    return "\n".join(entries) + "\n"


def _area_entries(repo: Path, rel: str) -> dict[int, str] | None:
    """Entries by number: a ``N. `` line and its indented continuation lines."""
    path = _inside(repo, rel)
    if path is None:
        return None
    entries: dict[int, list[str]] = {}
    current: list[str] | None = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if match := _ENTRY_START.match(line):
            number = int(match[1])
            current = None if number in entries else entries.setdefault(number, [line])
        elif current is not None and line[:1].isspace() and line.strip():
            current.append(line)
        else:
            current = None
    return {number: "\n".join(lines) for number, lines in entries.items()}


def _inside(repo: Path, rel: str) -> Path | None:
    """``repo / rel`` if it is a file inside ``repo``; ``None`` for anything else."""
    forms = (PurePosixPath(rel), PureWindowsPath(rel))
    if any(form.is_absolute() or form.drive or ".." in form.parts for form in forms):
        return None
    root = repo.resolve()
    try:
        path = (root / rel).resolve()
    except (OSError, RuntimeError):
        return None
    return path if path.is_relative_to(root) and path.is_file() else None


def _read(path: Path) -> str | None:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None
