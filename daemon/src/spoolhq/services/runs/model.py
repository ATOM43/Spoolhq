"""Statuses, kinds and the frozen records the run log returns."""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from spoolhq.core.tokens import weighted_tokens


class RunStatus(StrEnum):
    RUNNING = "running"
    PAUSED = "paused"
    """Waiting for a subscription usage limit to reset."""
    AWAITING_APPROVAL = "awaiting_approval"
    """A PR or local approval is pending; survives restarts."""
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"

    @property
    def is_terminal(self) -> bool:
        return self in TERMINAL_RUN_STATUSES


TERMINAL_RUN_STATUSES = frozenset(
    {RunStatus.DONE, RunStatus.BLOCKED, RunStatus.CANCELLED, RunStatus.INTERRUPTED}
)


class RunKind(StrEnum):
    TICKET = "ticket"
    PLAN = "plan"
    """The planner turning the spec into draft tickets; its ``ticket_id`` is ``plan``."""


PLAN_RUN_ID = "plan"
"""The ``ticket_id`` of every plan run, and the folder of its attempts (``runs/plan/``)."""


class AttemptKind(StrEnum):
    INITIAL = "initial"
    GATE_RETRY = "gate_retry"
    REVIEW_RETRY = "review_retry"
    CONFLICT_RETRY = "conflict_retry"
    PR_CHANGES = "pr_changes"
    PLAN = "plan"


class AttemptStatus(StrEnum):
    RUNNING = "running"
    GATES_FAILED = "gates_failed"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    NEEDS_HUMAN = "needs_human"
    CONFLICT = "conflict"
    ERROR = "error"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


class EventKind(StrEnum):
    RUN_STARTED = "run.started"
    RUN_STATUS = "run.status"
    RUN_INTERRUPTED = "run.interrupted"
    RUN_PHASE = "run.phase"
    ATTEMPT_STARTED = "attempt.started"
    ATTEMPT_FINISHED = "attempt.finished"
    AGENT_MESSAGE = "agent.message"
    AGENT_TOOL_CALL = "agent.tool_call"
    AGENT_FILE_EDIT = "agent.file_edit"
    AGENT_USAGE = "agent.usage"
    GATE_RESULT = "gate.result"
    REVIEW_VERDICT = "review.verdict"
    LOG = "log"
    INTEGRATE = "integrate"


@dataclass(frozen=True)
class Run:
    """One execution of the loop for one ticket, from being picked until it ends."""

    id: int
    ticket_id: str
    status: RunStatus
    reason: str | None
    daemon_instance: str
    started_at: str
    ended_at: str | None
    progress_note: str | None = None
    """The implementer's ``<progress>`` note from its last completed attempt, for T14."""
    reset_at: str | None = None
    """When a run paused by a usage limit may resume; ``None`` otherwise."""
    kind: RunKind = RunKind.TICKET


@dataclass(frozen=True)
class Attempt:
    """One implementer pass inside a run, with its gates and review.

    ``number`` counts per ticket across all its runs; ``dir`` is the attempt folder
    relative to the workspace (``runs/T04/003``), which ``workspace`` locates.
    """

    id: int
    run_id: int
    ticket_id: str
    number: int
    kind: AttemptKind
    status: AttemptStatus
    dir: str
    backend: str | None
    model: str | None
    input_tokens: int
    output_tokens: int
    cost_micro_usd: int | None
    started_at: str
    ended_at: str | None
    workspace: Path = field(repr=False, compare=False)
    cache_read_tokens: int = 0
    """The part of ``input_tokens`` read from the prompt cache."""


@dataclass(frozen=True)
class Event:
    """An append-only record; ``id`` increases across the whole workspace."""

    id: int
    run_id: int
    attempt_id: int | None
    ts: str
    kind: EventKind
    payload: dict[str, Any]


@dataclass(frozen=True)
class Usage:
    """Summed tokens and cost; the cost is None when no attempt reported one."""

    input_tokens: int
    output_tokens: int
    cost_micro_usd: int | None
    cache_read_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def weighted_tokens(self) -> int:
        """What ``agents.budget_per_ticket.tokens`` counts: cache reads at a tenth."""
        return weighted_tokens(self.input_tokens, self.output_tokens, self.cache_read_tokens)
