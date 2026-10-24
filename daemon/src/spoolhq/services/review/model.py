"""The reviewer's inputs and result, as frozen values.

``ReviewInputs`` has no field for the implementer's transcript, summary or progress
note on purpose: the reviewer judges the code, not the implementer's claims about it.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from spoolhq.services.agents import Outcome

Verdict = Literal["approve", "changes_requested", "needs_human"]
VERDICTS: tuple[Verdict, ...] = ("approve", "changes_requested", "needs_human")


@dataclass(frozen=True)
class GateLine:
    name: str
    command: str
    status: str
    """The gate's status: ``passed``, ``failed``, ``timed_out``, ``skipped`` or ``error``."""


@dataclass(frozen=True)
class ReviewInputs:
    ticket_id: str
    title: str
    body: str
    done_when: tuple[str, ...]
    """The ``## Done when`` items, as written; item ``1`` is ``done_when[0]``."""
    gate_checked: Mapping[int, bool]
    """Item index → the gates' result, only for items the gates checked."""
    diff: str
    """``git diff <base>...HEAD`` of the committed work."""
    gate_summary: tuple[GateLine, ...]
    worktree: Path
    """Absolute; the reviewer's working directory, which it can read but not change."""


@dataclass(frozen=True)
class ItemVerdict:
    index: int
    item: str
    """The "Done when" item's text."""
    met: bool
    reason: str
    source: Literal["reviewer", "gates"]


@dataclass(frozen=True)
class ReviewResult:
    run_outcome: Outcome
    verdict: Verdict | None
    """``None`` when the run didn't complete; ``run_outcome`` says why."""
    items: tuple[ItemVerdict, ...]
    summary: str
    attempts: int
    invalid_errors: tuple[str, ...]
    """Why an attempt's output was rejected, each prefixed ``attempt N: ``."""
    diff_trimmed: bool
    input_tokens: int
    output_tokens: int
    cost_micro_usd: int | None
    reset_at: datetime | None
    cache_read_tokens: int = 0

    def unmet(self) -> tuple[ItemVerdict, ...]:
        """The items that are not met, for T10's ``review_notes`` on a retry."""
        return tuple(item for item in self.items if not item.met)
