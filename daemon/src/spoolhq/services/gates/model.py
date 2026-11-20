"""Gate results: one per configured command, and the run of all three."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal, TypedDict

GateName = Literal["install", "lint", "test", "file_size", "test_guard", "secret_scan"]
"""The three command gates, plus the built-in ones: file size (``size.py``), the test
guard (``test_guard.py``) and the secret scan (``secrets.py``)."""
GATE_NAMES: tuple[GateName, ...] = ("install", "lint", "test")
"""The command gates, in the order they run."""


class GateStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"
    ERROR = "error"
    """The program wasn't found or couldn't start."""


GATE_OK = (GateStatus.PASSED, GateStatus.SKIPPED)
"""A skipped gate is one whose command isn't set (or install failed, which fails the run)."""


class GateFailureData(TypedDict):
    """The fields of T10's ``GateFailure``, so the run loop can build one from it."""

    command: str
    exit_code: int | None
    timed_out: bool
    output_excerpt: str


@dataclass(frozen=True)
class FileChange:
    """One file a ticket adds, changes, renames or deletes, read by the caller from git."""

    path: str
    """The path after the ticket (the old one for a deleted file)."""
    before: bytes | None
    """The content before the ticket; ``None`` for a new file."""
    deleted: bool = False
    old_path: str | None = None
    """The path before a rename."""
    added: tuple[tuple[int, str], ...] = ()
    """The added lines, as (line number in the new file, text)."""


@dataclass(frozen=True)
class GateResult:
    name: GateName
    command: str
    status: GateStatus
    exit_code: int | None
    """``None`` when the command timed out, was skipped or couldn't start."""
    duration_s: float
    excerpt: str
    """The trimmed output of a gate that didn't pass (the error for ``error``)."""
    failing_tests: tuple[str, ...]
    output_lines: int
    output_truncated: bool
    log_path: Path | None
    """The full output; ``None`` when the command never ran."""
    excerpt_trimmed: bool = False
    """``excerpt`` is shorter than the output (``build_excerpt`` cut lines from it)."""


@dataclass(frozen=True)
class GateRun:
    results: tuple[GateResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.status in GATE_OK for result in self.results)

    @property
    def first_failure(self) -> GateResult | None:
        return next(
            (
                result
                for result in self.results
                if result.status not in (GateStatus.PASSED, GateStatus.SKIPPED)
            ),
            None,
        )

    def to_gate_failures(self) -> tuple[GateFailureData, ...]:
        """The failed and timed-out gates, shaped like T10's ``GateFailure``."""
        return tuple(
            GateFailureData(
                command=result.command,
                exit_code=result.exit_code,
                timed_out=result.status is GateStatus.TIMED_OUT,
                output_excerpt=result.excerpt,
            )
            for result in self.results
            if result.status in (GateStatus.FAILED, GateStatus.TIMED_OUT)
        )


@dataclass(frozen=True)
class DoneWhenCheck:
    item: str
    """The "Done when" line."""
    command: str
    """The backticked command in it."""
    status: Literal["passed", "failed", "not_a_gate"]
