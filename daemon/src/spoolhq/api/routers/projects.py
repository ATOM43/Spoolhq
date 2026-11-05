"""Project endpoints: list, read and create projects (``spool init``), edit
``project.yaml`` and ``CONTEXT.md`` with ETags, and try a stack command (token required)."""

import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, Response, Security, status

from spoolhq.api.errors import ApiError, service_errors
from spoolhq.api.params import (
    IfMatch,
    ProjectName,
    require_if_match,
    run_log,
    settings,
    workspace,
)
from spoolhq.api.schemas.projects import (
    CommandTest,
    CommandTestResult,
    CreateProject,
    IdleView,
    JobStarted,
    ProjectDetail,
    ProjectSummary,
    SettingsFile,
    SettingsProblem,
    SpecFile,
    UsageTotal,
)
from spoolhq.api.schemas.runs import RunView
from spoolhq.api.security import bearer_scheme
from spoolhq.services.creation import CreationError, CreationJobs
from spoolhq.services.gates import try_command
from spoolhq.services.projects import (
    CONTEXT_FILE,
    NO_TEST_COMMAND,
    EditConflict,
    Project,
    ProjectError,
    ProjectValidationError,
    has_spec,
    list_workspaces,
    load_project,
    parse_project,
    read_with_etag,
    save_project,
    split_error,
    write_if_match,
)
from spoolhq.services.projects.yaml_io import write_atomic
from spoolhq.services.runloop import RunLoop, RunLoopError
from spoolhq.services.runs import RunLogError, latest_phase, project_totals
from spoolhq.services.scheduler import PlanError, explain_idle, next_ready, remaining_hours
from spoolhq.services.tickets import TicketListing, list_tickets

router = APIRouter(prefix="/api/projects", dependencies=[Security(bearer_scheme)])
NEEDS_YOU = ("awaiting_approval", "blocked")
# Below the desktop app's 120 s request timeout; a run uses the project's own timeouts.
COMMAND_TEST_TIMEOUT_S = 90.0


def _load(
    folder: Path, name: str, request: Request
) -> tuple[Project | None, SettingsProblem | None]:
    """The project's settings, or the first problem of its ``project.yaml``."""
    try:
        return load_project(name, projects_dir=settings(request).projects_dir), None
    except ProjectValidationError as exc:
        field, message = split_error(exc.errors[0])
    except ProjectError as exc:
        field, message = None, str(exc)
    return None, SettingsProblem(file=str(folder / "project.yaml"), field=field, message=message)


def _creating(request: Request, name: str) -> ProjectSummary | None:
    """A project a creation job still holds: reported as such, its files left alone."""
    jobs: CreationJobs = request.app.state.creation
    job_id = jobs.running(name)
    if job_id is None:
        return None
    return ProjectSummary(
        name=name, done=0, total=0, run_state="creating", needs_you=0, job_id=job_id
    )


def _summary(request: Request, name: str) -> tuple[ProjectSummary, TicketListing, Project | None]:
    folder = workspace(request, name)
    # Read first: an event written while the rest is read is then replayed after it.
    try:
        log = run_log(request, name)
        latest_seq = log.last_event_id()
        totals = project_totals(log)
    except (RunLogError, sqlite3.Error):
        log, latest_seq, totals = None, 0, None
    with service_errors():
        listing = list_tickets(name, projects_dir=settings(request).projects_dir)
    statuses = [ticket.meta.status for ticket in listing.tickets]
    project, problem = _load(folder, name, request)
    run, step, run_state = None, None, "idle"
    if project is not None:
        loop: RunLoop = request.app.state.runloop
        try:
            current = loop.current(name)
        except RunLoopError:
            current = None
        if current is not None and current.run is not None:
            run = RunView.of(current.run)
            step = latest_phase(log, current.run.id) if log is not None else None
            run_state = current.run.status.value if current.active else "idle"
    try:
        remaining = remaining_hours(listing.tickets)
    except PlanError:
        remaining = 0.0
    cost = totals.cost_micro_usd if totals else None
    summary = ProjectSummary(
        name=name,
        done=statuses.count("done"),
        total=len(statuses),
        run_state=run_state,
        needs_you=sum(status in NEEDS_YOU for status in statuses),
        latest_seq=latest_seq,
        draft=statuses.count("draft"),
        remaining_h=remaining,
        has_spec=has_spec(name, projects_dir=settings(request).projects_dir),
        template=project.template.name if project and project.template else None,
        run=run,
        run_step=step,
        last_activity=totals.last_activity if totals else None,
        usage=UsageTotal(
            tokens=totals.tokens if totals else 0,
            cost_usd=None if cost is None else cost / 1_000_000,
        ),
        settings_error=problem,
    )
    return summary, listing, project


def _left_behind(request: Request) -> dict[str, ProjectSummary]:
    """Per project, the latest ended creation whose rollback left paths behind."""
    jobs: CreationJobs = request.app.state.creation
    return {
        job.project: ProjectSummary(
            name=job.project,
            done=0,
            total=0,
            run_state="cleanup_failed",
            needs_you=0,
            job_id=job.id,
            left=job.rollback.left if job.rollback else [],
        )
        for job in sorted(jobs.left_behind(), key=lambda job: job.ended_at or 0.0)
    }


@router.get("")
def list_projects(request: Request) -> list[ProjectSummary]:
    """Every workspace; a project whose creation left paths behind is listed as
    ``cleanup_failed`` instead (also when its workspace is gone)."""
    left = _left_behind(request)
    listed = [
        _creating(request, path.name)
        or left.pop(path.name, None)
        or _summary(request, path.name)[0]
        for path in list_workspaces(settings(request).projects_dir)
    ]
    return listed + list(left.values())


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def create_project(body: CreateProject, request: Request) -> JobStarted:
    """Check the request (422 with its field) and start the creation job."""
    jobs: CreationJobs = request.app.state.creation
    try:
        job = jobs.start(body)
    except CreationError as exc:
        raise ApiError(422, "validation_error", exc.message, field=exc.field) from exc
    return JobStarted(job_id=job.id)


@router.get("/{name}")
def get_project(name: ProjectName, request: Request) -> ProjectDetail:
    if creating := _creating(request, name):
        return ProjectDetail(
            **creating.model_dump(), repo=None, default_branch=None, remote=None, invalid_tickets=0
        )
    summary, listing, project = _summary(request, name)
    tickets, next_ticket, idle = listing.tickets, None, None
    try:
        if tickets:
            ready, reason = next_ready(tickets), explain_idle(tickets)
            next_ticket = ready.id if ready else None
            if reason is not None:
                idle = IdleView(
                    code=reason.code, ticket_ids=list(reason.ticket_ids), message=reason.message
                )
    except PlanError as exc:
        idle = IdleView(code="invalid_plan", ticket_ids=[], message=str(exc))
    if project is not None and project.commands.test is None:
        next_ticket = None
        idle = IdleView(code="no_commands", ticket_ids=[], message=NO_TEST_COMMAND)
    return ProjectDetail(
        **summary.model_dump(),
        repo=str(project.repo) if project else None,
        default_branch=project.default_branch if project else None,
        remote=project.git.remote if project else None,
        invalid_tickets=len(listing.invalid),
        next_ticket=next_ticket,
        idle=idle,
    )


def _settings_data(name: str, request: Request) -> dict[str, Any]:
    with service_errors():
        project = load_project(name, projects_dir=settings(request).projects_dir)
    return project.model_dump(mode="json", exclude_unset=True)


@router.get("/{name}/settings")
def get_settings(name: ProjectName, request: Request, response: Response) -> SettingsFile:
    path = workspace(request, name) / "project.yaml"
    response.headers["ETag"] = read_with_etag(path)[1]
    return SettingsFile(settings=_settings_data(name, request))


@router.put("/{name}/settings")
def put_settings(
    name: ProjectName,
    body: SettingsFile,
    request: Request,
    response: Response,
    if_match: IfMatch = None,
) -> SettingsFile:
    folder = workspace(request, name)
    expected = require_if_match(if_match)
    with service_errors():
        project = parse_project(name, body.settings)
        try:
            response.headers["ETag"] = write_if_match(
                folder,
                folder / "project.yaml",
                expected,
                lambda: save_project(project, projects_dir=settings(request).projects_dir),
            )
        except EditConflict as exc:
            raise _conflict(exc, SettingsFile(settings=_settings_data(name, request))) from exc
    return SettingsFile(settings=_settings_data(name, request))


@router.get("/{name}/spec")
def get_spec(name: ProjectName, request: Request, response: Response) -> SpecFile:
    data, etag = read_with_etag(workspace(request, name) / CONTEXT_FILE)
    response.headers["ETag"] = etag
    return SpecFile(content=data.decode("utf-8", errors="replace"))


@router.put("/{name}/spec")
def put_spec(
    name: ProjectName,
    body: SpecFile,
    request: Request,
    response: Response,
    if_match: IfMatch = None,
) -> SpecFile:
    folder = workspace(request, name)
    path = folder / CONTEXT_FILE
    try:
        response.headers["ETag"] = write_if_match(
            folder, path, require_if_match(if_match), lambda: write_atomic(path, body.content)
        )
    except EditConflict as exc:
        current = SpecFile(content=exc.data.decode("utf-8", errors="replace"))
        raise _conflict(exc, current) from exc
    return body


@router.post("/{name}/commands/test")
def try_stack_command(name: ProjectName, body: CommandTest, request: Request) -> CommandTestResult:
    """Run ``command`` once in the project's repository, without a shell, with the gates'
    environment and a 90 s timeout. It may change the checkout, as the gate would."""
    workspace(request, name)
    with service_errors():
        project = load_project(name, projects_dir=settings(request).projects_dir)
    result = try_command(body.gate, body.command, Path(project.repo), COMMAND_TEST_TIMEOUT_S)
    return CommandTestResult(
        status=result.status.value,  # type: ignore[arg-type]  # never skipped here
        exit_code=result.exit_code,
        duration_s=round(result.duration_s, 3),
        output=result.excerpt,
        output_truncated=result.output_truncated,
        timeout_s=COMMAND_TEST_TIMEOUT_S,
    )


def _conflict(exc: EditConflict, current: Any) -> ApiError:
    return ApiError(412, "edit_conflict", str(exc), etag=exc.etag, current=current.model_dump())
