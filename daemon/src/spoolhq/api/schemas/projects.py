"""Request and response models of the project, settings and spec endpoints."""

from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, Field

from spoolhq.services.gates import check_gate_command


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
    latest_seq: int = 0
    """The newest stored event's ``seq`` (0 if none), read before the rest of this answer:
    subscribe with ``since=latest_seq`` to get every later change without a replay."""


class IdleView(BaseModel):
    """Why no ticket can run now (``spool run next`` says the same)."""

    code: Literal[
        "all_done",
        "running",
        "awaiting_approval",
        "blocked",
        "waiting",
        "plan_not_approved",
        "invalid_plan",
    ]
    ticket_ids: list[str]
    message: str


class ProjectDetail(ProjectSummary):
    repo: str
    default_branch: str
    remote: str | None
    invalid_tickets: int
    """Ticket files that don't load (``spool plan check`` lists them)."""
    next_ticket: str | None = None
    """The ticket ``run/next`` would start; null when none can run (see ``idle``)."""
    idle: IdleView | None = None
    """Why nothing can run; null when ``next_ticket`` is set or there are no tickets."""
    remaining_h: float = 0
    """Estimated hours of the tickets not done (0 for an invalid plan)."""


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


class CommandTest(BaseModel):
    """A stack command to try in the project's repository, as its gate would run it."""

    gate: Literal["install", "lint", "test"]
    command: Annotated[
        str, Field(min_length=1, max_length=4096), AfterValidator(check_gate_command)
    ]
    """An argument list as text (``just lint``); shell syntax is refused (422)."""


class CommandTestResult(BaseModel):
    status: Literal["passed", "failed", "timed_out", "error"]
    """``error``: the program wasn't found or couldn't start."""
    exit_code: int | None
    duration_s: float
    output: str
    """The trimmed output (the error message for ``error``)."""
    output_truncated: bool
    timeout_s: float
