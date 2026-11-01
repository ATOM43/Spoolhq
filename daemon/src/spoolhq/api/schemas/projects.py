"""Request and response models of the project, settings and spec endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class ProjectSummary(BaseModel):
    name: str
    done: int
    """Tickets in status ``done``."""
    total: int
    """Valid tickets of the plan."""
    run_state: str
    """The active run's status (``running``, ``paused``), else ``idle``."""
    needs_you: int
    """Tickets waiting for a person: ``awaiting_approval`` or ``blocked``."""


class ProjectDetail(ProjectSummary):
    repo: str
    default_branch: str
    remote: str | None
    invalid_tickets: int
    """Ticket files that don't load (``spool plan check`` lists them)."""


class CreateProject(BaseModel):
    """What ``spool init`` takes."""

    name: str = Field(pattern=r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
    repo: str = Field(min_length=1, max_length=4096)
    """An existing git repository; with ``template``, a new or empty folder to generate into."""
    branch: str = "main"
    remote: str | None = None
    template: str | None = None
    """A built-in template name, a folder or a git URL."""
    template_ref: str | None = None


class ProjectCreated(BaseModel):
    name: str
    path: str
    missing_notes: list[str]
    """Code-facing notes the repository doesn't have (SpoolHQ never writes them)."""


class SettingsFile(BaseModel):
    settings: dict[str, Any]
    """``project.yaml`` as data, validated by the project model."""


class SpecFile(BaseModel):
    content: str = Field(max_length=900_000)
    """``CONTEXT.md``, exactly as stored."""
