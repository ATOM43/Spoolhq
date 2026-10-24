"""Fitting the trimmable inputs into the prompt's character budget.

Pure, deterministic functions. Each trimmer gets the text and the room it may use (the
kept text plus its note line) and returns what to keep and a one-line note saying what
was cut, or no note if nothing was.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass

GATE_EXCERPT_MAX = 8_000
GATE_EXCERPT_HEAD = 6_000
GATE_EXCERPT_TAIL = 2_000
CLAUDE_MD_CAP = 16_000
PROGRESS_CAP = 24_000
DECISIONS_CAP = 24_000
MIN_CONTEXT_ROOM = 2_000
# Room kept free for a note line ("[trimmed: …]\n"); the longest note is under 70.
NOTE_RESERVE = 100

_ENTRY_HEADING = "## "
_OUTLINE_RE = re.compile(r"#{1,2}\s")
_WORD_RE = re.compile(r"[a-z0-9]+")
_MIN_WORD = 4


@dataclass(frozen=True)
class Trimmed:
    text: str
    """What to keep; empty means nothing fits and the block is left out."""
    note: str | None = None
    """``[trimmed: …]`` when something was cut, else ``None``."""


def cap_excerpt(text: str) -> str:
    """Cap a gate's output at 8,000 characters: the first 6,000 and the last 2,000."""
    if len(text) <= GATE_EXCERPT_MAX:
        return text
    cut = len(text) - GATE_EXCERPT_HEAD - GATE_EXCERPT_TAIL
    head, tail = text[:GATE_EXCERPT_HEAD], text[-GATE_EXCERPT_TAIL:]
    return f"{head}\n[… {cut:,} characters cut …]\n{tail}"


def words(text: str) -> set[str]:
    """Distinct lower-case ``[a-z0-9]`` words of at least four characters."""
    return {word for word in _WORD_RE.findall(text.lower()) if len(word) >= _MIN_WORD}


def _lines(text: str) -> list[str]:
    if text and not text.endswith("\n"):
        text += "\n"
    return text.splitlines(keepends=True)


def _total(lines: Iterable[str]) -> int:
    return sum(len(line) for line in lines)


def keep_head(text: str, room: int, *, cap: int | None = None) -> Trimmed:
    """Keep the beginning of ``text``, cut at a line boundary."""
    limit = room if cap is None else min(cap, room)
    if len(text) <= limit:
        return Trimmed(text)
    avail = min(limit, room - NOTE_RESERVE)
    kept: list[str] = []
    for line in _lines(text):
        if _total(kept) + len(line) > avail:
            break
        kept.append(line)
    if not kept:
        return Trimmed("")
    size = _total(kept)
    return Trimmed("".join(kept), f"[trimmed: kept the first {size:,} of {len(text):,} characters]")


def newest_entries(text: str, count: int) -> str:
    """The preamble and the newest ``count`` ``## `` entries; all of a file without any."""
    lines = _lines(text)
    starts = [i for i, line in enumerate(lines) if line.startswith(_ENTRY_HEADING)]
    if len(starts) <= count:
        return text
    return "".join(lines[: starts[0]] + lines[starts[-count] :])


def newest_lines(text: str, count: int) -> str:
    """From the ``count``-th last non-blank line to the end."""
    lines = _lines(text)
    seen = 0
    for i in range(len(lines) - 1, -1, -1):
        seen += bool(lines[i].strip())
        if seen == count:
            return "".join(lines[i:])
    return text


def keep_newest_entries(text: str, room: int, *, cap: int) -> Trimmed:
    """Keep the newest ``## `` entries (the last in the file), then the preamble if it fits.

    A file with no level-2 headings keeps its last whole lines.
    """
    if len(text) <= min(cap, room):
        return Trimmed(text)
    avail = min(cap, room - NOTE_RESERVE)
    lines = _lines(text)
    starts = [i for i, line in enumerate(lines) if line.startswith(_ENTRY_HEADING)]

    if not starts:
        kept: list[str] = []
        for line in reversed(lines):
            if _total(kept) + len(line) > avail:
                break
            kept.append(line)
        if not kept:
            return Trimmed("")
        kept.reverse()
        return Trimmed(
            "".join(kept), f"[trimmed: kept the last {len(kept):,} of {len(lines):,} lines]"
        )

    preamble = "".join(lines[: starts[0]])
    bounds = [*starts, len(lines)]
    entries = ["".join(lines[a:b]) for a, b in zip(bounds, bounds[1:], strict=False)]
    chosen: list[str] = []
    for entry in reversed(entries):
        if _total(chosen) + len(entry) > avail:
            break
        chosen.append(entry)
    if not chosen:
        return Trimmed("")
    chosen.reverse()
    with_preamble = bool(preamble) and _total(chosen) + len(preamble) <= avail
    kept_text = (preamble if with_preamble else "") + "".join(chosen)
    if len(chosen) < len(entries):
        note = f"[trimmed: kept the last {len(chosen):,} of {len(entries):,} entries]"
    else:
        note = f"[trimmed: kept all {len(entries):,} entries, left out the preamble]"
    return Trimmed(kept_text, note)


def select_spec(text: str, room: int, *, ticket_words: set[str]) -> Trimmed:
    """The whole spec if it fits; otherwise its outline plus the most relevant sections.

    The outline is every ``#`` and ``##`` heading line. Sections (split at ``## ``) are
    ranked by how many distinct words they share with the ticket, ties in document
    order, and added until the next one does not fit; they keep their document order.
    """
    if len(text) <= room:
        return Trimmed(text)
    avail = room - NOTE_RESERVE
    lines = _lines(text)
    starts = [i for i, line in enumerate(lines) if line.startswith(_ENTRY_HEADING)]
    if not starts:
        return keep_head(text, room)

    preamble = lines[: starts[0]]
    bounds = [*starts, len(lines)]
    sections = [lines[a:b] for a, b in zip(bounds, bounds[1:], strict=False)]

    def outline(part: list[str]) -> list[str]:
        return [line for line in part if _OUTLINE_RE.match(line)]

    size = _total(outline(preamble)) + sum(_total(outline(s)) for s in sections)
    if size > avail:
        return keep_head(text, room)

    scores = [len(words("".join(section)) & ticket_words) for section in sections]
    selected: set[int] = set()
    for index in sorted(range(len(sections)), key=lambda i: (-scores[i], i)):
        extra = _total(sections[index]) - _total(outline(sections[index]))
        if size + extra > avail:
            break
        selected.add(index)
        size += extra

    kept = outline(preamble)
    for index, section in enumerate(sections):
        kept.extend(section if index in selected else outline(section))
    note = f"[trimmed: kept the outline and {len(selected):,} of {len(sections):,} sections]"
    return Trimmed("".join(kept), note)
