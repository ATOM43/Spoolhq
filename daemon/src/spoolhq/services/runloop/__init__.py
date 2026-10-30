"""Run loop: takes one ready ticket through worktree → implementer → gates → reviewer.

``RunLoop`` runs each project's active run in a worker thread inside the daemon, with
retries, pause, resume (after a usage limit or a crash), cancel and discard, and hands
an approved attempt to an ``Integrator`` (``Delivery``: one squash commit on the local
default branch or GitHub, unless the merge policy in ``policy.py`` wants a person). The
state machine itself is plain functions over a ``RunContext`` in ``machine.py``. This is
the one service that imports the others; no service imports it. See ``docs/run-loop.md``.
"""

from spoolhq.services.runloop.approval import approve, reject
from spoolhq.services.runloop.delivery import Delivery
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
from spoolhq.services.runloop.policy import (
    DeliveryMode,
    PolicyDecision,
    RuleHit,
    delivery_mode,
    describe,
    evaluate,
    path_matches,
)
from spoolhq.services.runloop.polling import GitHubPoller
from spoolhq.services.runloop.resume import RESUME_DELAY, ResumeTimer

__all__ = [
    "RESUME_DELAY",
    "RUN_LOCK",
    "Agents",
    "Current",
    "Delivery",
    "DeliveryMode",
    "EndKind",
    "Ending",
    "Flags",
    "GitHubPoller",
    "HoldForIntegration",
    "IntegrationResult",
    "IntegrationStatus",
    "Integrator",
    "LocalIntegrator",
    "Merged",
    "Mode",
    "NotFoundError",
    "PlanJobs",
    "PolicyDecision",
    "ResumeTimer",
    "RunActiveError",
    "RunContext",
    "RunLoop",
    "RunLoopError",
    "RuleHit",
    "approve",
    "delivery_mode",
    "describe",
    "drive",
    "evaluate",
    "next_kind",
    "path_matches",
    "recover_integrations",
    "reject",
    "take_run_lock",
]
