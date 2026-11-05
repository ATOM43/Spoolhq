"""Request and response models of the project, settings and spec endpoints."""

from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, Field

from spoolhq.api.schemas.runs import RunView
from spoolhq.services.creation import CreateProject, StackCommands
from spoolhq.services.gates import check_gate_command

__all__ = ["CreateProject", "StackCommands"]  # the request model lives in the service


class SettingsProblem(BaseModel):
    """The first problem of a ``project.yaml`` that doesn't load."""

    file: str
    """The file's absolute path."""
    field: str | None
    """The dotted path of the setting, like ``merge_policy.max_diff_lines``; null for a
    problem with the whole file (unreadable, not YAML, empty)."""
    message: str


class UsageTotal(BaseModel):
    """Usage over every attempt of the project, planner included."""

    tokens: int = 0
    """Tokens of the attempts that reported no cost (subscription backends)."""
    cost_usd: float | None = None
    """The summed cost of the attempts that reported one (API-key backends); null if none."""


class ProjectSummary(BaseModel):
    name: str
    done: int
    """Tickets in status ``done``."""
    total: int
    """Valid tickets of the plan."""
    run_state: str
    """The active run's status (``running``, ``paused``), ``creating`` while a creation
    job holds the project (see ``job_id``), ``cleanup_failed`` when a failed or cancelled
    creation left paths behind (see ``left``), else ``idle``."""
    needs_you: int
    """Tickets waiting for a person: ``awaiting_approval`` or ``blocked``."""
    latest_seq: int = 0
    """The newest stored event's ``seq`` (0 if none), read before the rest of this answer:
    subscribe with ``since=latest_seq`` to get every later change without a replay."""
    draft: int = 0
    """Tickets in status ``draft``: the plan waits for approval."""
    remaining_h: float = 0
    """Estimated hours of the tickets not done (0 for an invalid plan)."""
    has_spec: bool = False
    """``CONTEXT.md`` exists and isn't blank."""
    template: str | None = None
    """The stack template the repository was generated from; null for an existing repo."""
    run: RunView | None = None
    """The active run, else the latest one; null before the first run or while
    ``settings_error`` is set."""
    run_step: str | None = None
    """The phase ``run`` is on or ended in (``implement``, ``gates``, ``review``, …)."""
    last_activity: str | None = None
    """When the latest event was written; null before the first one."""
    usage: UsageTotal = Field(default_factory=UsageTotal)
    settings_error: SettingsProblem | None = None
    """Set when ``project.yaml`` doesn't load; the project is listed anyway."""
    job_id: str | None = None
    """While ``run_state`` is ``creating`` or ``cleanup_failed``: the creation job.
    Nothing else is read then, so the other fields keep their defaults."""
    left: list[str] = Field(default_factory=list)
    """For ``cleanup_failed``: the paths the rollback couldn't delete. Listed for an
    hour after the job ended, or until ``POST /api/jobs/{id}/dismiss``."""


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
        "no_commands",
    ]
    ticket_ids: list[str]
    message: str


class ProjectDetail(ProjectSummary):
    repo: str | None
    """Null while ``settings_error`` is set (as are ``default_branch`` and ``remote``)."""
    default_branch: str | None
    remote: str | None
    invalid_tickets: int
    """Ticket files that don't load (``spool plan check`` lists them)."""
    next_ticket: str | None = None
    """The ticket ``run/next`` would start; null when none can run (see ``idle``)."""
    idle: IdleView | None = None
    """Why nothing can run; null when ``next_ticket`` is set or there are no tickets."""


class JobStarted(BaseModel):
    job_id: str
    """Poll ``GET /api/jobs/{job_id}`` while it runs."""


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
