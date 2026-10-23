"""Request and response models of the run endpoints."""

from typing import Literal

from pydantic import BaseModel

from spoolhq.services.runloop import Current
from spoolhq.services.runs import Run


class StartRun(BaseModel):
    mode: Literal["next", "all"] = "next"
    ticket: str | None = None
    """Run this ticket (it must be ready) instead of the next ready one; ``next`` only."""


class RunView(BaseModel):
    id: int
    ticket_id: str
    status: str
    reason: str | None
    started_at: str
    ended_at: str | None
    reset_at: str | None
    progress_note: str | None

    @classmethod
    def of(cls, run: Run) -> "RunView":
        return cls(
            id=run.id,
            ticket_id=run.ticket_id,
            status=run.status.value,
            reason=run.reason,
            started_at=run.started_at,
            ended_at=run.ended_at,
            reset_at=run.reset_at,
            progress_note=run.progress_note,
        )


class PhaseLine(BaseModel):
    id: int
    """The event id; ids only grow, so a client prints the lines above the last it saw."""
    text: str


class CurrentRun(BaseModel):
    project: str
    active: bool
    """A run is running or paused."""
    working: bool
    """A worker thread is on it (false once it ends or pauses)."""
    run: RunView | None
    """The active run, else the project's latest run."""
    attempts: int
    input_tokens: int
    output_tokens: int
    phases: list[PhaseLine]

    @classmethod
    def of(cls, current: Current) -> "CurrentRun":
        usage = current.usage
        return cls(
            project=current.project,
            active=current.active,
            working=current.working,
            run=RunView.of(current.run) if current.run is not None else None,
            attempts=current.attempts,
            input_tokens=usage.input_tokens if usage else 0,
            output_tokens=usage.output_tokens if usage else 0,
            phases=[PhaseLine(id=event_id, text=text) for event_id, text in current.phases],
        )


class Discarded(BaseModel):
    ticket_id: str
    status: Literal["ready"] = "ready"
