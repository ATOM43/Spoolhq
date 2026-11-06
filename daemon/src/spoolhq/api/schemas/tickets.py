"""Request and response models of the ticket endpoints."""

from dataclasses import asdict
from typing import Literal

from pydantic import BaseModel, Field

from spoolhq.api.schemas.runs import AttemptView, Reject, RunView
from spoolhq.services.runloop import TicketRuns
from spoolhq.services.runs import TicketActivity
from spoolhq.services.tickets import InvalidTicket, Ticket, TicketMeta


class TicketActivityView(BaseModel):
    attempts: int
    tokens: int
    """Tokens of attempts without a cost (subscription backends)."""
    cost_micro_usd: int | None
    """Summed cost of attempts with one (API-key backends); null if none."""
    run_id: int | None
    """The ticket's latest run."""
    reason: str | None
    """That run's reason: why it is blocked or waits for approval."""

    @classmethod
    def of(cls, activity: TicketActivity) -> "TicketActivityView":
        return cls(**asdict(activity))


class TicketView(BaseModel):
    id: str
    file_name: str
    meta: TicketMeta
    """The frontmatter."""
    body: str
    """Everything after the frontmatter, exactly as stored."""
    activity: TicketActivityView | None = None
    """In the list only: the ticket's runs so far; null before its first run."""

    @classmethod
    def of(cls, ticket: Ticket, activity: TicketActivity | None = None) -> "TicketView":
        return cls(
            id=ticket.id,
            file_name=ticket.file_name,
            meta=ticket.meta,
            body=ticket.body,
            activity=TicketActivityView.of(activity) if activity else None,
        )


class TicketAttemptView(AttemptView):
    run_id: int


class TicketGitView(BaseModel):
    branch: str | None
    """The ticket's local branch, while it exists."""
    commits: int | None
    """Commits on that branch ahead of the default branch."""
    diff_lines: int | None
    """Lines those commits add and remove."""
    commit: str | None
    """The squash commit on the default branch, once merged."""
    commit_url: str | None
    """That commit on GitHub, with a GitHub remote."""
    tag: str | None
    pr_number: int | None
    pr_url: str | None
    pr_state: Literal["open", "merged", "closed"] | None
    pr_checked_at: str | None
    """When the project's open pull requests were last checked (this daemon's run)."""


class TicketDetail(TicketView):
    """``GET …/tickets/{id}``: the ticket with its latest run, attempts and git state."""

    run: RunView | None
    """The latest run: its reason, the merge-policy rules that fired, its pull request."""
    attempts: list[TicketAttemptView]
    """Every attempt of the ticket, oldest first."""
    git: TicketGitView

    @classmethod
    def of_runs(cls, view: TicketView, runs: TicketRuns) -> "TicketDetail":
        return cls(
            **view.model_dump(),
            run=RunView.of(runs.run) if runs.run else None,
            attempts=[
                TicketAttemptView(**AttemptView.of(a).model_dump(), run_id=a.run_id)
                for a in runs.attempts
            ],
            git=TicketGitView(**asdict(runs.git)),
        )


class InvalidTicketView(BaseModel):
    file_name: str
    errors: list[str]

    @classmethod
    def of(cls, invalid: InvalidTicket) -> "InvalidTicketView":
        return cls(file_name=invalid.file_name, errors=invalid.errors)


class TicketList(BaseModel):
    tickets: list[TicketView]
    invalid: list[InvalidTicketView]
    """Files that don't load, whatever the filters."""


class TicketUpdate(BaseModel):
    meta: TicketMeta
    body: str = Field(max_length=900_000)


class Note(Reject):
    reset_retries: bool = True
    """Give the run its full gate and review retries again."""
