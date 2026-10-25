"""Run loop: takes one ready ticket through worktree → implementer → gates → reviewer.

``RunLoop`` runs each project's active run in a worker thread inside the daemon, with
retries, pause, resume (after a usage limit or a crash), cancel and discard, and hands
an approved attempt to an ``Integrator`` (``LocalIntegrator``: one squash commit on the
local default branch). The state machine itself is plain functions
over a ``RunContext`` in ``machine.py``. This is the one service that imports the
others; no service imports it. See ``docs/run-loop.md``.
"""

from spoolhq.services.runloop.integration import LocalIntegrator, recover_integrations
from spoolhq.services.runloop.integrator import (
    HoldForIntegration,
    IntegrationResult,
    IntegrationStatus,
    Integrator,
)
from spoolhq.services.runloop.lock import RUN_LOCK, take_run_lock
from spoolhq.services.runloop.loop import Mode, RunLoop
from spoolhq.services.runloop.machine import drive, next_kind
from spoolhq.services.runloop.model import (
    Agents,
    Current,
    Ending,
    EndKind,
    Flags,
    Merged,
    NotFoundError,
    RunActiveError,
    RunContext,
    RunLoopError,
)
from spoolhq.services.runloop.planning import PlanJobs
from spoolhq.services.runloop.resume import RESUME_DELAY, ResumeTimer

__all__ = [
    "RESUME_DELAY",
    "RUN_LOCK",
    "Agents",
    "Current",
    "EndKind",
    "Ending",
    "Flags",
    "HoldForIntegration",
    "IntegrationResult",
    "IntegrationStatus",
    "Integrator",
    "LocalIntegrator",
    "Merged",
    "Mode",
    "NotFoundError",
    "PlanJobs",
    "ResumeTimer",
    "RunActiveError",
    "RunContext",
    "RunLoop",
    "RunLoopError",
    "drive",
    "next_kind",
    "recover_integrations",
    "take_run_lock",
]
