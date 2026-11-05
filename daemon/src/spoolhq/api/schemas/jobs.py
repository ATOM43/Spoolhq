"""Response models of the job endpoints."""

from typing import Literal

from pydantic import BaseModel

from spoolhq.services.creation import Job


class StepView(BaseModel):
    name: Literal["workspace", "repo", "commands", "commit"]
    title: str
    state: Literal["pending", "running", "passed", "failed", "skipped"]
    duration_s: float | None
    message: str | None
    """For a failure: a fixed message."""
    output: str | None
    """For a failure: the trimmed output or error."""
    field: str | None
    """For a failure: the request field that caused it, like ``commands.test``."""


class RollbackView(BaseModel):
    removed: list[str]
    """What the job had created and deleted again, newest first."""
    left: list[str]
    """What it couldn't delete; empty when the rollback is complete."""


class JobView(BaseModel):
    id: str
    project: str
    source: Literal["template", "existing", "empty"]
    state: Literal["running", "succeeded", "failed", "cancelled"]
    steps: list[StepView]
    rollback: RollbackView | None
    """Set after a failure or cancel."""

    @classmethod
    def of(cls, job: Job) -> "JobView":
        return cls.model_validate(
            {
                "id": job.id,
                "project": job.project,
                "source": job.source,
                "state": job.state,
                "steps": [vars(step) for step in job.steps],
                "rollback": vars(job.rollback) if job.rollback else None,
            }
        )
