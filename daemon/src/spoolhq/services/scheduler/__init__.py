"""Scheduler: the plan as a whole.

Checks the dependency graph (unknown dependencies, cycles, duplicate ids), owns the
table of allowed status changes, picks the ticket that runs next and explains why none
can, and computes the progress figures. Everything here is pure logic over a list of
``Ticket``s except ``apply_transition``, which saves through the tickets store. The
rules are described in ``docs/scheduler.md``.
"""

from spoolhq.core.ids import id_key
from spoolhq.services.scheduler.errors import (
    PlanError,
    PlanProblem,
    ProblemCode,
    SchedulerError,
    TransitionError,
)
from spoolhq.services.scheduler.graph import validate_plan
from spoolhq.services.scheduler.progress import (
    CriticalPath,
    PlanSummary,
    critical_path,
    remaining_hours,
    summary,
)
from spoolhq.services.scheduler.schedule import (
    IdleCode,
    IdleReason,
    explain_idle,
    next_ready,
    waiting_on,
)
from spoolhq.services.scheduler.transitions import (
    TRANSITIONS,
    TransitionResult,
    apply_transition,
    check_transition,
    parse_status,
)

__all__ = [
    "TRANSITIONS",
    "CriticalPath",
    "IdleCode",
    "IdleReason",
    "PlanError",
    "PlanProblem",
    "PlanSummary",
    "ProblemCode",
    "SchedulerError",
    "TransitionError",
    "TransitionResult",
    "apply_transition",
    "check_transition",
    "critical_path",
    "explain_idle",
    "id_key",
    "next_ready",
    "parse_status",
    "remaining_hours",
    "summary",
    "validate_plan",
    "waiting_on",
]
