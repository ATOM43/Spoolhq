"""Request and response models of the run endpoints."""

from typing import Any, Literal

from pydantic import BaseModel

from spoolhq.services.runloop import Current, Merged, describe
from spoolhq.services.runs import Run


class StartRun(BaseModel):
    mode: Literal["next", "all"] = "next"
    ticket: str | None = None
    """Run this ticket (it must be ready) instead of the next ready one; ``next`` only."""


class Reject(BaseModel):
    note: str = ""
    """What should change; required (an empty note is refused with 409)."""


class RuleHitView(BaseModel):
    rule: str
    detail: str


class PolicyView(BaseModel):
    """The run's latest merge-policy decision."""

    mode: str
    """``direct``, ``pr`` or ``approval``."""
    rules: list[RuleHitView]
    summary: str
    """``needs you: diff_size (812 lines > 400), …``; empty when no rule holds."""

    @classmethod
    def of(cls, policy: dict[str, Any]) -> "PolicyView":
        rules = policy.get("rules", [])
        return cls(
            mode=str(policy.get("mode", "")),
            rules=[RuleHitView(rule=r["rule"], detail=r["detail"]) for r in rules],
            summary=describe(rules),
        )


class RunView(BaseModel):
    id: int
    kind: str
    ticket_id: str
    status: str
    reason: str | None
    started_at: str
    ended_at: str | None
    reset_at: str | None
    progress_note: str | None
    pr_number: int | None = None
    """The pull request the run was delivered as (GitHub delivery)."""
    pr_url: str | None = None
    policy: PolicyView | None = None
    """The merge policy's latest decision for the run (T18)."""

    @classmethod
    def of(cls, run: Run) -> "RunView":
        return cls(
            id=run.id,
            kind=run.kind.value,
            ticket_id=run.ticket_id,
            status=run.status.value,
            reason=run.reason,
            started_at=run.started_at,
            ended_at=run.ended_at,
            reset_at=run.reset_at,
            progress_note=run.progress_note,
            pr_number=run.pr_number,
            pr_url=run.pr_url,
            policy=PolicyView.of(run.policy) if run.policy is not None else None,
        )


class PhaseLine(BaseModel):
    id: int
    """The event id; ids only grow, so a client prints the lines above the last it saw."""
    text: str


class MergedView(BaseModel):
    ticket_id: str
    commit: str
    """The squash commit's full sha on the default branch."""
    tag: str

    @classmethod
    def of(cls, merged: Merged) -> "MergedView":
        return cls(ticket_id=merged.ticket_id, commit=merged.commit, tag=merged.tag)


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
    last_merged: MergedView | None = None
    """The ticket the project's latest finished integration merged."""

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
            last_merged=MergedView.of(current.last_merged) if current.last_merged else None,
        )


class Discarded(BaseModel):
    ticket_id: str
    status: Literal["ready"] = "ready"
