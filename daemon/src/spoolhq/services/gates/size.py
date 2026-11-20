"""The file-size gate: no file a ticket adds or changes may end up over the line limit.

Built in, so it holds in every project, including repos without a line check of their
own. Lines are counted like SpoolHQ's ``scripts/check_line_limit.py``
(``len(text.splitlines())``). A file already over the limit before the ticket may stay
there as long as it doesn't grow. Binary files (a NUL byte) are skipped. The caller gets
each changed path with its old content from git, so this package stays git-free.
"""

import time
from collections.abc import Iterable, Sequence
from fnmatch import fnmatchcase
from pathlib import Path

from spoolhq.services.gates.model import GateName, GateResult, GateStatus

FILE_SIZE: GateName = "file_size"
DEFAULT_MAX_FILE_LINES = 500
LOCKFILE_PATTERNS = ("**/*.lock", "**/*-lock.*")
DEFAULT_EXEMPT = (*LOCKFILE_PATTERNS, "**/*.min.*")


def count_lines(data: bytes) -> int | None:
    """The line count, or ``None`` for a binary file."""
    if b"\0" in data:
        return None
    return len(data.decode("utf-8", errors="replace").splitlines())


def is_exempt(path: str, patterns: Iterable[str]) -> bool:
    """``**/`` also matches at the top level, so ``**/*.lock`` covers ``uv.lock``."""
    return any(
        fnmatchcase(path, pattern) or (pattern.startswith("**/") and fnmatchcase(path, pattern[3:]))
        for pattern in patterns
    )


def check_file_sizes(
    worktree: Path,
    changed: Iterable[tuple[str, bytes | None]],
    limit: int,
    exempt: Sequence[str] = DEFAULT_EXEMPT,
) -> GateResult:
    """``changed``: each added or changed path and its content before the ticket (``None``
    for a new file). ``limit`` 0 skips the gate."""
    command = f"max {limit} lines per file"
    start = time.monotonic()
    problems: list[str] = []
    if limit:
        for path, old in changed:
            target = worktree / path
            if is_exempt(path, exempt) or target.is_symlink() or not target.is_file():
                continue
            lines = count_lines(target.read_bytes())
            if lines is None or lines <= limit:
                continue
            before = None if old is None else count_lines(old)
            if before is None or before <= limit:
                problems.append(f"{path}: {lines} lines, over the {limit}-line limit")
            elif lines > before:
                problems.append(
                    f"{path} grew from {before} to {lines} lines; it was already over the limit"
                )
    if not limit:
        status = GateStatus.SKIPPED
    else:
        status = GateStatus.FAILED if problems else GateStatus.PASSED
    return GateResult(
        name=FILE_SIZE,
        command=command if limit else "",
        status=status,
        exit_code=None,
        duration_s=time.monotonic() - start,
        excerpt="\n".join(problems),
        failing_tests=(),
        output_lines=len(problems),
        output_truncated=False,
        log_path=None,
    )
