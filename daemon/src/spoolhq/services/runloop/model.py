"""The run loop's values: the context one run works in, how it ends, and its errors."""

import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from spoolhq.core.daemon_lock import DaemonLock
from spoolhq.services.agents import AgentRunner
from spoolhq.services.gates import GateRun
from spoolhq.services.git import GitError, Worktree, WorktreeManager
from spoolhq.services.projects import Agents as AgentSettings
from spoolhq.services.projects import Project, ProjectError
from spoolhq.services.runs import Attempt, EventKind, Run, RunLog, Usage
from spoolhq.services.scheduler import SchedulerError
from spoolhq.services.tickets import Ticket, TicketError

if TYPE_CHECKING:
    from spoolhq.services.runloop.integrator import Integrator

GatesFn = Callable[[Path, Mapping[str, str], Mapping[str, float], Path], GateRun]
"""``run_gates(worktree, commands, timeouts, log_dir)``; tests pass a fake."""


class RunLoopError(Exception):
    """A request the run loop refuses: nothing to run, a run already active, a bad state."""


@contextmanager
def user_errors() -> Iterator[None]:
    """Errors from the other services become RunLoopError, whose message is for the user."""
    try:
        yield
    except (ProjectError, TicketError, SchedulerError, GitError) as exc:
        raise RunLoopError(str(exc)) from exc


class NotFoundError(RunLoopError):
    """An unknown project, run or ticket."""


class RunActiveError(RunLoopError):
    """A run is already active in the project."""


@dataclass(frozen=True)
class Agents:
    """The runner for each role. The daemon builds them per project from ``project.yaml``
    (``for_project``); tests may pass fixed ``FakeRunner``s instead."""

    implementer: AgentRunner
    reviewer: AgentRunner
    planner: AgentRunner | None = None
    """The planner's runner; ``None`` uses the implementer's."""

    @classmethod
    def for_project(cls, settings: AgentSettings) -> "Agents":
        """Each role's backend from ``agents.*``, with ``agents.backends``' endpoint."""
        return cls(
            implementer=settings.runner_for("implementer"),
            reviewer=settings.runner_for("reviewer"),
            planner=settings.runner_for("planner"),
        )


class EndKind(StrEnum):
    DONE = "done"
    """Approved and merged."""
    HELD = "awaiting_approval"
    """Approved and held for integration (the default until T14)."""
    BLOCKED = "blocked"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    STOPPED = "stopped"
    """The daemon is shutting down; startup recovery marks the run interrupted."""


@dataclass(frozen=True)
class Ending:
    kind: EndKind
    reason: str | None = None
    reset_at: datetime | None = None


@dataclass
class Flags:
    """Requests from other threads, checked by the worker between steps."""

    cancel: threading.Event = field(default_factory=threading.Event)
    """Also passed to the agent, so a cancel stops it at once."""
    pause: threading.Event = field(default_factory=threading.Event)
    stop: threading.Event = field(default_factory=threading.Event)


@dataclass
class RunContext:
    """Everything one run works with. ``run`` and ``ticket`` are refreshed as they change."""

    project: Project
    workspace: Path
    projects_dir: Path
    home: Path
    ticket: Ticket
    run: Run
    run_log: RunLog
    worktrees: WorktreeManager
    worktree: Worktree
    agents: Agents
    integrator: "Integrator"
    gates: GatesFn
    flags: Flags

    @property
    def ticket_id(self) -> str:
        return self.ticket.id

    def phase(self, name: str, text: str, attempt: Attempt | None = None) -> None:
        """Record a phase change (``run.phase``); ``text`` is the line the CLI prints."""
        record_phase(self.run_log, self.run.id, name, text, attempt)


@dataclass
class Active:
    """A project's active run: working (``thread`` set) or paused."""

    ticket_id: str
    run_id: int
    flags: Flags
    thread: threading.Thread | None = None
    lock: DaemonLock | None = None


@dataclass(frozen=True)
class Merged:
    """The last ticket merged into the default branch: its squash commit and tag."""

    ticket_id: str
    commit: str
    tag: str


@dataclass(frozen=True)
class Current:
    """``runs/current``: the active run, or the project's latest one."""

    project: str
    active: bool
    working: bool
    run: Run | None
    attempts: int
    usage: Usage | None
    phases: tuple[tuple[int, str], ...]
    """``(event id, line)`` for each phase change of ``run``."""
    last_merged: Merged | None = None
    """The most recently finished integration in the project, if any."""


def record_phase(
    run_log: RunLog, run_id: int, name: str, text: str, attempt: Attempt | None = None
) -> None:
    """Append a ``run.phase`` event; ``text`` is the line ``spool run`` prints."""
    run_log.append_event(
        run_id,
        EventKind.RUN_PHASE,
        {"phase": name, "text": text},
        attempt_id=attempt.id if attempt is not None else None,
    )
