"""Gate output: cleaning, the first failure, the excerpt and failing test names (pure)."""

import re

EXCERPT_CHARS = 8_000
HEAD_LINES = 20
TAIL_LINES = 40
BEFORE_FAILURE_LINES = 30
# Character budgets per part, so a few huge lines can't crowd out the rest.
HEAD_CHARS = 1_200
TAIL_CHARS = 3_000
BEFORE_FAILURE_CHARS = 1_500
FAILURE_LINE_CHARS = 1_000
MARKER_RESERVE = 100  # at most three cut markers

# CSI (colours, cursor moves), OSC (titles, links), charset selection and the
# two-character escapes.
_ANSI_RE = re.compile(
    r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[()][0-9A-Za-z]|\x1b[@-Z\\-_]"
)
_PYTEST_RE = re.compile(r"(?:FAILED|ERROR) (.+)")
_VITEST_RE = re.compile(r"FAIL +(\S.* > .*\S)")


def clean(text: str) -> str:
    """``text`` without ANSI escape codes and with ``\\n`` line endings."""
    return _ANSI_RE.sub("", text).replace("\r\n", "\n")


def split_lines(text: str) -> list[str]:
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _priority(line: str) -> int | None:
    """Lower is stronger; ``None`` when the line isn't a failure line."""
    if line.startswith(("FAILED ", "ERROR ")):
        return 0
    if "Traceback (most recent call last)" in line:
        return 1
    # Vitest and Jest indent their FAIL and × lines.
    if line.lstrip().startswith(("FAIL ", "×", "✗")):
        return 2
    if "error[" in line or " error TS" in line or ": error:" in line:
        return 3
    if "error:" in line:
        return 4
    return None


def first_failure(lines: list[str]) -> int | None:
    """The index of the first line of the strongest failure kind present."""
    best: tuple[int, int] | None = None
    for index, line in enumerate(lines):
        priority = _priority(line)
        if priority is not None and (best is None or priority < best[0]):
            best = (priority, index)
            if priority == 0:
                break
    return None if best is None else best[1]


def _clip(line: str, size: int) -> str:
    return line if len(line) <= size else line[: max(size - 1, 0)] + "…"


def build_excerpt(text: str, limit: int = EXCERPT_CHARS) -> str:
    """The head, the window around the first failure and the tail, at most ``limit`` chars.

    Parts never overlap, stay in output order and are separated by ``[… N lines cut …]``.
    Output that fits is returned unchanged.
    """
    if len(text) <= limit:
        return text
    lines = split_lines(text)
    count = len(lines)
    chosen: dict[int, str] = {}

    def take(indices: range | list[int], budget: int) -> int:
        """Add lines in ``indices`` order until one doesn't fit; returns the chars used."""
        used = 0
        for index in indices:
            if index in chosen:
                continue
            cost = len(lines[index]) + 1
            if used + cost > budget:
                if used == 0:  # one huge line: keep its start
                    chosen[index] = _clip(lines[index], budget - 1)
                    used = budget
                break
            chosen[index] = lines[index]
            used += cost
        return used

    used = take(range(min(HEAD_LINES, count)), HEAD_CHARS)
    failure = first_failure(lines)
    if failure is None:
        tail_budget = limit - used - MARKER_RESERVE
        take(list(reversed(range(max(count - TAIL_LINES, 0), count))), tail_budget)
    else:
        used += take(list(reversed(range(max(count - TAIL_LINES, 0), count))), TAIL_CHARS)
        used += take([failure], FAILURE_LINE_CHARS)
        used += take(
            list(reversed(range(max(failure - BEFORE_FAILURE_LINES, 0), failure))),
            BEFORE_FAILURE_CHARS,
        )
        take(range(failure + 1, count), limit - used - MARKER_RESERVE)

    parts: list[str] = []
    previous = -1
    for index in sorted(chosen):
        if index > previous + 1:
            parts.append(f"[… {index - previous - 1} lines cut …]")
        parts.append(chosen[index])
        previous = index
    if previous < count - 1:
        parts.append(f"[… {count - 1 - previous} lines cut …]")
    return "\n".join(parts)


def failing_tests(text: str) -> tuple[str, ...]:
    """pytest node ids and Vitest ``file > test`` names, in output order, deduplicated."""
    names: list[str] = []
    for line in split_lines(text):
        pytest_match = _PYTEST_RE.fullmatch(line)
        if pytest_match:
            names.append(pytest_match[1].partition(" - ")[0].strip())
            continue
        vitest_match = _VITEST_RE.fullmatch(line.strip())
        if vitest_match:
            names.append(vitest_match[1])
    return tuple(dict.fromkeys(name for name in names if name))
