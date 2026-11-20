"""Converting an old flat ``DECISIONS.md`` to the split layout, on a project's first merge.

A flat file is a heading and intro, then entries: a line starting ``N. `` (numbered) or
``- ``/``* `` (unnumbered) at the left margin, followed by indented or blank lines. Each
entry moves word for word to ``docs/decisions/general.md`` as ``NNN. <rest of its first
line>`` with its other lines unchanged, keeping its number; unnumbered entries get the
numbers after the highest, in order of appearance. ``DECISIONS.md`` keeps its intro and
becomes the index. A file with index lines, or without entries, isn't touched. A
``PROGRESS.md`` needs nothing here: ``write_notes`` adds its markers at the end.
"""

import re
from pathlib import Path

from spoolhq.services.notes.write import (
    DECISIONS,
    DECISIONS_DIR,
    END,
    ENTRY_LINE,
    INDEX_LINE,
    PROGRESS,
    START,
    read_note_file,
    write_note_file,
)

GENERAL = f"{DECISIONS_DIR}/general.md"
_BULLET = re.compile(r"[-*] (.*)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")


class ConversionError(Exception):
    """The flat ``DECISIONS.md`` can't be split into entries; nothing was written."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"DECISIONS.md couldn't be converted: {reason}")


def _title(rest: str) -> str:
    bold = _BOLD.match(rest)
    return (bold[1] if bold else rest).strip()


def _parse(text: str) -> tuple[list[str], list[tuple[int | None, list[str]]]]:
    """The intro lines, and each entry's number (None if unnumbered) and lines, the first
    without its ``N. `` or bullet marker."""
    intro: list[str] = []
    entries: list[tuple[int | None, list[str]]] = []
    for number, line in enumerate(text.splitlines(), 1):
        numbered, bullet = ENTRY_LINE.match(line), _BULLET.match(line)
        if numbered or bullet:
            rest = numbered[2] if numbered else bullet[1] if bullet else ""
            if not rest.strip():
                raise ConversionError(f"line {number} is an entry without a title")
            entries.append((int(numbered[1]) if numbered else None, [rest]))
        elif not entries:
            intro.append(line)
        elif not line.strip() or line[0] in " \t":
            entries[-1][1].append(line)
        else:
            raise ConversionError(f"line {number} isn't part of an entry: {line.strip()[:60]}")
    return intro, entries


def convert_notes(repo: Path) -> tuple[list[str], list[str]]:
    """Convert a flat ``DECISIONS.md`` in ``repo``: the files written and one line per
    change for the commit body (also the ``PROGRESS.md`` markers ``write_notes`` will
    add). Raises ``ConversionError`` before writing anything."""
    summary: list[str] = []
    progress = read_note_file(repo, PROGRESS)
    if progress is not None and not any(
        line.strip() in (START, END) for line in progress.splitlines()
    ):
        summary.append("PROGRESS.md: added the spoolhq:recent markers at the end")
    text = read_note_file(repo, DECISIONS)
    if text is None or any(INDEX_LINE.fullmatch(line.strip()) for line in text.splitlines()):
        return [], summary
    intro, entries = _parse(text)
    if not entries:
        return [], summary
    numbers = [n for n, _ in entries if n is not None]
    if duplicates := sorted({n for n in numbers if numbers.count(n) > 1}):
        raise ConversionError(f"entry {duplicates[0]} appears more than once")
    next_number = max(numbers, default=0)
    area = read_note_file(repo, GENERAL) or "# Decisions · general\n"
    index = ("\n".join(intro).strip("\r\n") or "# Decisions") + "\n\n"
    for number, lines in entries:
        if number is None:
            next_number += 1
            number = next_number
        body = "\n".join([f"{number:03d}. {lines[0]}", *lines[1:]]).rstrip() + "\n"
        area += ("" if area.endswith("\n") else "\n") + "\n" + body
        index += f"{number:03d} · {_title(lines[0])} · {GENERAL}\n"
    write_note_file(repo, GENERAL, area)
    write_note_file(repo, DECISIONS, index)
    summary.append(
        f"DECISIONS.md: moved {len(entries)} entries word for word to {GENERAL}; "
        "DECISIONS.md is now the index"
    )
    return [DECISIONS, GENERAL], summary
