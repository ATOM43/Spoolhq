"""The test guard: a ticket may not delete, remove, skip or focus tests, or lower coverage.

Test files match ``gates.test_paths``. Tests are found by name: ``def test…`` in Python,
a named ``it(``/``test(`` in JS/TS. A removal or added marker passes only when a "Done
when" item names that exact test file or test name. The caller reads the changes from
git (``FileChange``), so this package stays git-free. See ``docs/gates.md#test-guard``.
"""

import re
import time
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from spoolhq.services.gates.model import FileChange, GateName, GateResult, GateStatus
from spoolhq.services.gates.size import is_exempt

TEST_GUARD: GateName = "test_guard"
DEFAULT_TEST_PATHS = ("**/tests/**", "**/test_*.py", "**/*_test.py", "**/*.test.*", "**/*.spec.*")
COVERAGE_DROP = 0.5
"""How many points below main's total a ticket's total may fall."""
# The most specific first: the first marker found on a line is the one reported.
MARKERS = (
    "pytest.mark.skip",
    "pytest.skip(",
    "unittest.skip",
    "xfail",
    "xdescribe(",
    "xit(",
    ".skip(",
    ".only(",
)
JS_SUFFIXES = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts")
_PY_TEST = re.compile(r"^[ \t]*(?:async[ \t]+)?def[ \t]+(test\w*)[ \t]*\(", re.MULTILINE)
_JS_TEST = re.compile(r"""\b(?:it|test)(?:\.\w+)*\s*\(\s*(["'`])(.+?)\1""")


@dataclass(frozen=True)
class Coverage:
    """The ticket's total, main's stored one, and why the comparison is skipped."""

    total: float | None = None
    stored: float | None = None
    note: str = ""


def _tests(path: str, text: str) -> list[tuple[int, str]]:
    """Each test defined in ``text`` as (line number, name)."""
    if path.endswith(".py"):
        found = ((m.start(), m.group(1)) for m in _PY_TEST.finditer(text))
    elif path.endswith(JS_SUFFIXES):
        found = ((m.start(), m.group(2)) for m in _JS_TEST.finditer(text))
    else:
        return []
    return [(text.count("\n", 0, start) + 1, name) for start, name in found]


def _named(name: str, done_when: Sequence[str]) -> bool:
    pattern = re.compile(rf"(?<![\w/]){re.escape(name)}(?![\w/])")
    return any(pattern.search(item) for item in done_when)


def _test_at(tests: list[tuple[int, str]], line: int) -> str | None:
    """The test a marker on ``line`` belongs to: on that line, a few lines below it (a
    decorator), else the nearest one above."""
    below = [name for number, name in tests if line <= number <= line + 3]
    above = [name for number, name in tests if number < line]
    return below[0] if below else above[-1] if above else None


def _text(data: bytes | None) -> str:
    return "" if data is None else data.decode("utf-8", errors="replace")


def _file_problems(
    worktree: Path, change: FileChange, test_paths: Sequence[str], done_when: Sequence[str]
) -> list[str]:
    old_path = change.old_path or change.path
    was_test, is_test = is_exempt(old_path, test_paths), is_exempt(change.path, test_paths)
    if not (was_test or is_test) or _named(old_path, done_when) or _named(change.path, done_when):
        return []
    before = Counter(name for _, name in _tests(old_path, _text(change.before)))
    if change.deleted:
        if was_test and (not before or not all(_named(name, done_when) for name in before)):
            return [f"Deleted test file {change.path}"]
        return []
    target = worktree / change.path
    after_text = "" if target.is_symlink() or not target.is_file() else _text(target.read_bytes())
    tests = _tests(change.path, after_text)
    problems = [
        f"Removed test {name} in {old_path}"
        for name in before - Counter(name for _, name in tests)
        if not _named(name, done_when)
    ]
    if is_test:
        for line, text in change.added:
            marker = next((m for m in MARKERS if m in text), None)
            if marker is None:
                continue
            test = _test_at(tests, line)
            if test is not None and _named(test, done_when):
                continue
            where = f" ({test})" if test else ""
            problems.append(f"Added {marker} in {change.path}:{line}{where}")
    return problems


def check_tests(
    worktree: Path,
    changes: Iterable[FileChange],
    test_paths: Sequence[str],
    done_when: Sequence[str],
    coverage: Coverage,
) -> GateResult:
    """Fail on a deleted test file, a removed test, an added skip or focus marker, or a
    coverage total more than ``COVERAGE_DROP`` points below main's."""
    start = time.monotonic()
    problems = [
        problem
        for change in changes
        for problem in _file_problems(worktree, change, test_paths, done_when)
    ]
    notes = [coverage.note] if coverage.note else []
    if coverage.total is not None and coverage.stored is not None:
        if round(coverage.stored - coverage.total, 6) > COVERAGE_DROP:
            problems.append(f"Coverage fell from {coverage.stored:.1f}% to {coverage.total:.1f}%")
        else:
            notes.append(f"Coverage {coverage.total:.1f}% (main {coverage.stored:.1f}%)")
    lines = problems + notes
    return GateResult(
        name=TEST_GUARD,
        command="test guard",
        status=GateStatus.FAILED if problems else GateStatus.PASSED,
        exit_code=None,
        duration_s=time.monotonic() - start,
        excerpt="\n".join(lines),
        failing_tests=(),
        output_lines=len(lines),
        output_truncated=False,
        log_path=None,
    )
