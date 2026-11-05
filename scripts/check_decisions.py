"""Fail when DECISIONS.md (the index) and docs/decisions/*.md (the entries) disagree.

Run by `just lint`. Checks that every index number has exactly one entry in the area
files and the reverse, that numbers run 1..N without gaps or duplicates, that each
index line names the file its entry is in, and that each index title is the entry's
bold heading. Standard library only, so it runs before any dependency is installed.
"""

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_LINE = re.compile(r"(\d{3,}) · (.+) · (docs/decisions/[a-z0-9-]+\.md)")
ENTRY_LINE = re.compile(r"(\d+)\. \*\*(.+?)\*\*")


def problems(root: Path) -> list[str]:
    index_file = root / "DECISIONS.md"
    found: list[str] = []
    index: list[tuple[int, str, str]] = []
    for line in index_file.read_text(encoding="utf-8").splitlines():
        if match := INDEX_LINE.fullmatch(line):
            index.append((int(match[1]), match[2], match[3]))
        elif re.match(r"\d", line):
            found.append(f"DECISIONS.md: not `NNN · title · docs/decisions/<area>.md`: {line}")

    entries: dict[int, tuple[str, str]] = {}
    entry_counts: Counter[int] = Counter()
    for path in sorted((root / "docs" / "decisions").glob("*.md")):
        name = path.relative_to(root).as_posix()
        for line in path.read_text(encoding="utf-8").splitlines():
            if match := ENTRY_LINE.match(line):
                number = int(match[1])
                entry_counts[number] += 1
                entries.setdefault(number, (match[2], name))

    index_counts = Counter(number for number, _, _ in index)
    for number, count in sorted(index_counts.items()):
        if count > 1:
            found.append(f"DECISIONS.md: {number} is listed {count} times")
    for number, count in sorted(entry_counts.items()):
        if count > 1:
            found.append(f"docs/decisions: {number} has {count} entries")
    expected = set(range(1, max(index_counts, default=0) + 1))
    for number in sorted(expected - set(index_counts)):
        found.append(f"DECISIONS.md: {number} is missing (numbers must have no gaps)")
    for number in sorted(set(entries) - set(index_counts)):
        found.append(f"{entries[number][1]}: {number} is not in DECISIONS.md")

    for number, title, name in index:
        if number not in entries:
            found.append(f"DECISIONS.md: {number} has no entry in docs/decisions/")
            continue
        heading, actual = entries[number]
        if name != actual:
            found.append(f"DECISIONS.md: {number} points to {name}, but it is in {actual}")
        if title != heading:
            found.append(f"DECISIONS.md: {number} title {title!r} != heading {heading!r}")
    return found


def main() -> int:
    found = problems(ROOT)
    for problem in found:
        print(problem, file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
