"""Writing a merged ticket's notes into the repository, byte-exact outside what is added.

``PROGRESS.md``: the newest entries sit between the ``spoolhq:recent`` markers, newest
first; a sixth is moved, word for word, to the end of ``docs/progress-archive.md``.
Nothing outside the markers is rewritten. Decisions: with ``DECISIONS.md`` missing or an
index (split layout), each goes to ``docs/decisions/<area>.md`` as ``NNN. title`` with
its text indented, plus an index line; a flat ``DECISIONS.md`` gets the entry appended.
Files are read and written as bytes (``surrogateescape``), so undecodable bytes and line
endings survive. See ``docs/integration.md``.
"""

import re
from datetime import date
from pathlib import Path

from spoolhq.services.notes.note import Decision, RunNote, clean_title

PROGRESS = "PROGRESS.md"
DECISIONS = "DECISIONS.md"
ARCHIVE = "docs/progress-archive.md"
DECISIONS_DIR = "docs/decisions"
START = "<!-- spoolhq:recent:start -->"
END = "<!-- spoolhq:recent:end -->"
RECENT = 5
INDEX_LINE = re.compile(r"(\d+) · (.*) · ([^·]+\.md)")
ENTRY_LINE = re.compile(r"(\d+)\. (.*)")

_PROGRESS_HEADING = "# Progress\n"
_ARCHIVE_HEADING = "# Progress archive\n\nOlder PROGRESS.md entries, oldest first.\n"
_DECISIONS_HEADING = "# Decisions\n"


class NotesError(Exception):
    """The notes files can't be written as they are (broken markers, a path outside)."""


def _target(repo: Path, rel: str) -> Path:
    root = repo.resolve()
    path = (root / rel).resolve()
    if not path.is_relative_to(root):
        raise NotesError(f"{rel} points outside the repository")
    return path


def read_note_file(repo: Path, rel: str) -> str | None:
    path = _target(repo, rel)
    return path.read_bytes().decode("utf-8", "surrogateescape") if path.is_file() else None


def _write(repo: Path, rel: str, text: str) -> None:
    path = _target(repo, rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8", "surrogateescape"))


def _append(text: str, added: str) -> str:
    return text + ("" if not text or text.endswith("\n") else "\n") + added


def write_notes(
    repo: Path, ticket_id: str, title: str, note: RunNote, merged_on: date
) -> list[str]:
    """Write the ticket's progress entry and decisions; the repo-relative paths changed."""
    heading = f"### {ticket_id} · {clean_title(title)} ({merged_on.isoformat()})"
    written = _progress(repo, f"{heading}\n\n{note.progress}\n")
    return written + _decisions(repo, note.decisions)


def _progress(repo: Path, entry: str) -> list[str]:
    text = read_note_file(repo, PROGRESS) or _PROGRESS_HEADING
    if not any(line.strip() in (START, END) for line in text.splitlines()):
        text = _append(text, f"\n{START}\n{END}\n")
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.strip() == START]
    ends = [i for i, line in enumerate(lines) if line.strip() == END]
    if len(starts) != 1 or len(ends) != 1 or starts[0] > ends[0]:
        raise NotesError("PROGRESS.md needs exactly one spoolhq:recent start and end marker")
    first, last = starts[0], ends[0]
    head, entries = _entries(lines[first + 1 : last])
    entries.insert(0, entry)
    kept, moved = entries[:RECENT], entries[RECENT:]
    managed = "\n".join([*head, *kept])
    _write(
        repo, PROGRESS, "".join(lines[: first + 1]) + "\n" + managed + "\n" + "".join(lines[last:])
    )
    if not moved:
        return [PROGRESS]
    archive = read_note_file(repo, ARCHIVE) or _ARCHIVE_HEADING
    _write(repo, ARCHIVE, _append(archive, "".join(f"\n{old}" for old in reversed(moved))))
    return [PROGRESS, ARCHIVE]


def _entries(lines: list[str]) -> tuple[list[str], list[str]]:
    """The managed part's text before the first entry (kept if not blank) and its
    ``### `` entries, each without trailing blank lines."""
    chunks: list[list[str]] = [[]]
    for line in lines:
        if line.startswith("### "):
            chunks.append([])
        chunks[-1].append(line)
    head, *entries = ["".join(chunk).strip("\r\n") for chunk in chunks]
    return ([head + "\n"] if head.strip() else []), [e.rstrip() + "\n" for e in entries]


def _entry(number: int, decision: Decision) -> str:
    body = "".join(f"    {line}\n" for line in decision.text.splitlines())
    return f"{number:03d}. {decision.title}\n{body}"


def _decisions(repo: Path, decisions: tuple[Decision, ...]) -> list[str]:
    text = read_note_file(repo, DECISIONS)
    written = [DECISIONS] if text is None else []
    text = _DECISIONS_HEADING if text is None else text
    lines = text.splitlines()
    index = [int(m[1]) for line in lines if (m := INDEX_LINE.fullmatch(line.strip()))]
    flat = [int(m[1]) for line in lines if (m := ENTRY_LINE.match(line))]
    split = bool(index) or not flat
    number = max(index if split else flat, default=0)
    for decision in decisions:
        number += 1
        if not split:
            text = _append(text, "\n" + _entry(number, decision))
            continue
        rel = f"{DECISIONS_DIR}/{decision.area}.md"
        area = read_note_file(repo, rel) or f"# Decisions · {decision.area}\n"
        _write(repo, rel, _append(area, "\n" + _entry(number, decision)))
        last = next((line for line in reversed(text.splitlines()) if line.strip()), "")
        gap = "" if INDEX_LINE.fullmatch(last.strip()) else "\n"
        text = _append(text, f"{gap}{number:03d} · {decision.title} · {rel}\n")
        written.append(rel)
    if decisions or written:
        _write(repo, DECISIONS, text)
    return list(dict.fromkeys([*written, DECISIONS] if decisions else written))
