"""Request and response models of the plan endpoints."""

from pydantic import BaseModel, Field

from spoolhq.api.schemas.runs import RunView


class GeneratePlan(BaseModel):
    template_description: str | None = Field(default=None, max_length=200_000)
    """The applied stack template's description (untrusted); ``None`` until T16."""


class PlanStarted(BaseModel):
    run_id: int
    run: RunView


class PlanApproved(BaseModel):
    approved: list[str]
