"""Gate results: one per configured command, and the run of all three."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal, TypedDict

GateName = Literal["install", "lint", "test"]
GATE_NAMES: tuple[GateName, ...] = ("install", "lint", "test")


class GateStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"
    ERROR = "error"
    """The program wasn't found or couldn't start."""


class GateFailureData(TypedDict):
    """The fields of T10's ``GateFailure``, so the run loop can build one from it."""

    command: str
    exit_code: int | None
    timed_out: bool
    output_excerpt: str


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


@dataclass(frozen=True)
class GateRun:
    results: tuple[GateResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.status is GateStatus.PASSED for result in self.results)

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
