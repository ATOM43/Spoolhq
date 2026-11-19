"""Request and response models of the draft endpoints."""

from typing import Literal

from pydantic import BaseModel, Field

from spoolhq.api.schemas.tickets import TicketView
from spoolhq.services.planner import REQUEST_MAX
from spoolhq.services.runloop import DraftJob
from spoolhq.services.scheduler import DraftTicket


class DraftRequest(BaseModel):
    request: str = Field(min_length=1, max_length=REQUEST_MAX, pattern=r"\S")
    """A few lines saying what the tickets should do (untrusted)."""


class DraftStarted(BaseModel):
    job_id: str


class ProblemView(BaseModel):
    code: Literal["schema", "unknown_dependency", "cycle", "missing_done_when", "estimate_too_high"]
    message: str
    field: str
    """The draft's field to fix, like ``depends_on``."""


class DraftView(BaseModel):
    ref: Literal["D1", "D2", "D3"]
    title: str
    scope: str
    """Markdown, one ``- …`` line per scope bullet."""
    done_when: list[str]
    depends_on: list[str]
    """Existing ticket ids and other drafts' refs."""
    estimate_h: float
    review_required: bool
    phase: int
    problems: list[ProblemView]
    """Empty when the draft can be saved as it is."""


class DraftJobView(BaseModel):
    id: str
    project: str
    state: Literal["running", "succeeded", "failed", "cancelled"]
    error: str | None
    """After a failure: why, like "The planner's answer couldn't be read"."""
    run_id: int
    """The ``draft`` run that records the job's usage."""
    drafts: list[DraftView]
    """Once it succeeded: 1 to 3 drafts, in ref order."""

    @classmethod
    def of(cls, job: DraftJob) -> "DraftJobView":
        drafts = [
            {**vars(draft), "problems": [vars(problem) for problem in draft.problems]}
            for draft in job.drafts
        ]
        return cls.model_validate(
            {
                "id": job.id,
                "project": job.project,
                "state": job.state,
                "error": job.error,
                "run_id": job.run_id,
                "drafts": drafts,
            }
        )


class TicketBatch(BaseModel):
    tickets: list[DraftTicket] = Field(min_length=1, max_length=3)
    """The edited drafts, in ref order; ``depends_on`` may name the other drafts' refs."""


class TicketsSaved(BaseModel):
    tickets: list[TicketView]
    """The new tickets, in draft order."""
