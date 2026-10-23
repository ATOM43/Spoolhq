"""The integration seam: what happens to an approved attempt.

T14 provides the real integrator (rebase, squash-merge, tag, PROGRESS.md). Until then
``HoldForIntegration`` holds the approved work: the ticket and the run wait in
``awaiting_approval`` and the worktree is kept.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from spoolhq.services.runloop.model import RunContext


class IntegrationStatus(StrEnum):
    MERGED = "merged"
    CONFLICT = "conflict"
    FAILED = "failed"
    HELD = "held"
    """Not merged yet: waiting for integration or a person's approval."""


@dataclass(frozen=True)
class IntegrationResult:
    status: IntegrationStatus
    message: str = ""


class Integrator(Protocol):
    def integrate(self, ctx: RunContext) -> IntegrationResult: ...


class HoldForIntegration:
    """The default until T14: approved work waits in ``awaiting_approval``."""

    def integrate(self, ctx: RunContext) -> IntegrationResult:
        return IntegrationResult(
            IntegrationStatus.HELD,
            f"{ctx.ticket_id} approved; merging arrives in T14 — "
            f"worktree kept at {ctx.worktree.path}",
        )
