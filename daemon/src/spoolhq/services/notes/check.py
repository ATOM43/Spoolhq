"""Checking that ``DECISIONS.md``'s index and the area files agree.

Only the split layout has anything to match: a ``DECISIONS.md`` without index lines
(flat, or just a heading) passes. Every index line must have exactly one entry in
``docs/decisions/*.md`` and the reverse, numbers run 1..N without gaps or duplicates,
and each index title is its entry's heading (``N. title``, or the bold part of
``N. **title** …``).
"""

import re
from collections import Counter
from pathlib import Path

from spoolhq.services.notes.write import DECISIONS, DECISIONS_DIR, ENTRY_LINE, INDEX_LINE

_BOLD = re.compile(r"\*\*(.+?)\*\*")


def _heading(rest: str) -> str:
    bold = _BOLD.match(rest)
    return bold[1] if bold else rest.strip()


def notes_problems(repo: Path) -> list[str]:
    """Each way the index and the area files disagree, first problem first."""
    index_file = repo / DECISIONS
    if not index_file.is_file():
        return []
    index: list[tuple[int, str, str]] = []
    for line in index_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if match := INDEX_LINE.fullmatch(line.strip()):
            index.append((int(match[1]), match[2], match[3].strip()))
    if not index:
        return []
    entries: dict[int, tuple[str, str]] = {}
    entry_counts: Counter[int] = Counter()
    for path in sorted((repo / DECISIONS_DIR).glob("*.md")):
        name = f"{DECISIONS_DIR}/{path.name}"
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if match := ENTRY_LINE.match(line):
                number = int(match[1])
                entry_counts[number] += 1
                entries.setdefault(number, (_heading(match[2]), name))

    found: list[str] = []
    index_counts = Counter(number for number, _, _ in index)
    found += [f"DECISIONS.md: {n} is listed {c} times" for n, c in index_counts.items() if c > 1]
    found += [f"{DECISIONS_DIR}: {n} has {c} entries" for n, c in entry_counts.items() if c > 1]
    expected = set(range(1, max(index_counts) + 1))
    found += [f"DECISIONS.md: {n} is missing" for n in sorted(expected - set(index_counts))]
    found += [
        f"{entries[n][1]}: {n} is not in DECISIONS.md"
        for n in sorted(set(entries) - set(index_counts))
    ]
    for number, title, name in index:
        if number not in entries:
            found.append(f"DECISIONS.md: {number} has no entry in {DECISIONS_DIR}/")
            continue
        heading, actual = entries[number]
        if name != actual:
            found.append(f"DECISIONS.md: {number} points to {name}, but it is in {actual}")
        if title != heading:
            found.append(f"DECISIONS.md: {number} title {title!r} != heading {heading!r}")
    return found
