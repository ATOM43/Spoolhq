"""Request and response models of the plan endpoints."""

from pydantic import BaseModel, Field

from spoolhq.api.schemas.runs import RunView
from spoolhq.services.planner import PlanOverview, PlanState


class GeneratePlan(BaseModel):
    template_description: str | None = Field(default=None, max_length=200_000)
    """The applied stack template's description (untrusted); ``None`` until T16."""


class PlanStarted(BaseModel):
    run_id: int
    run: RunView


class PlanApproved(BaseModel):
    approved: list[str]


class PlanProblemView(BaseModel):
    code: str
    """``cycle``, ``unknown_dependency``, ``duplicate_id``, ``missing_done_when`` or
    ``invalid_ticket``."""
    message: str
    ticket_ids: list[str]
    """The tickets it is about; a cycle's members in work order."""


class PlanView(BaseModel):
    state: PlanState
    generated_at: str | None
    ticket_count: int
    """The drafts while ``state`` is ``draft``, else every ticket."""
    total_h: float
    problems: list[PlanProblemView]

    @classmethod
    def of(cls, plan: PlanOverview) -> "PlanView":
        return cls(
            state=plan.state,
            generated_at=plan.generated_at,
            ticket_count=plan.ticket_count,
            total_h=plan.total_h,
            problems=[
                PlanProblemView(code=p.code, message=p.message, ticket_ids=list(p.ticket_ids))
                for p in plan.problems
            ],
        )
