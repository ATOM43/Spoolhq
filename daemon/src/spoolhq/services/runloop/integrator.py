"""The integration seam: what happens to an approved attempt.

The real one is ``LocalIntegrator`` (``integration.py``). ``HoldForIntegration`` is for
projects with ``run.integration: hold``: the approved work waits in
``awaiting_approval`` with its worktree until ``spool run integrate``.
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
    GATES_FAILED = "gates_failed"
    """The gates failed on the merged code; ``message`` is the first failing command."""


@dataclass(frozen=True)
class IntegrationResult:
    status: IntegrationStatus
    message: str = ""


class Integrator(Protocol):
    def integrate(self, ctx: RunContext) -> IntegrationResult: ...


class HoldForIntegration:
    """``run.integration: hold``: approved work waits in ``awaiting_approval``."""

    def integrate(self, ctx: RunContext) -> IntegrationResult:
        return IntegrationResult(
            IntegrationStatus.HELD,
            f"{ctx.ticket_id} approved; merge it with `spool run integrate "
            f"{ctx.project.name} {ctx.ticket_id}` — worktree kept at {ctx.worktree.path}",
        )
