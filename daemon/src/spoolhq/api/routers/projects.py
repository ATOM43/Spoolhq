"""Project endpoints: list, read and create projects (``spool init``), edit
``project.yaml`` and ``CONTEXT.md`` with ETags, and try a stack command (token required)."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, Response, Security, status

from spoolhq.api.errors import ApiError, service_errors
from spoolhq.api.params import IfMatch, ProjectName, require_if_match, settings, workspace
from spoolhq.api.schemas.projects import (
    CommandTest,
    CommandTestResult,
    CreateProject,
    ProjectCreated,
    ProjectDetail,
    ProjectSummary,
    SettingsFile,
    SpecFile,
)
from spoolhq.api.security import bearer_scheme
from spoolhq.services.gates import try_command
from spoolhq.services.projects import (
    CONTEXT_FILE,
    EditConflict,
    InitResult,
    init_project,
    list_workspaces,
    load_project,
    parse_project,
    read_with_etag,
    save_project,
    write_if_match,
)
from spoolhq.services.projects.yaml_io import write_atomic
from spoolhq.services.runloop import RunLoop, RunLoopError
from spoolhq.services.templates import TemplateError, init_from_template
from spoolhq.services.tickets import list_tickets

router = APIRouter(prefix="/api/projects", dependencies=[Security(bearer_scheme)])
NEEDS_YOU = ("awaiting_approval", "blocked")
# Below the desktop app's 120 s request timeout; a run uses the project's own timeouts.
COMMAND_TEST_TIMEOUT_S = 90.0


def _summary(request: Request, name: str) -> tuple[ProjectSummary, int]:
    with service_errors():
        listing = list_tickets(name, projects_dir=settings(request).projects_dir)
    statuses = [ticket.meta.status for ticket in listing.tickets]
    loop: RunLoop = request.app.state.runloop
    try:
        current = loop.current(name)
        run_state = current.run.status.value if current.active and current.run else "idle"
    except RunLoopError:
        run_state = "unknown"
    summary = ProjectSummary(
        name=name,
        done=statuses.count("done"),
        total=len(statuses),
        run_state=run_state,
        needs_you=sum(status in NEEDS_YOU for status in statuses),
    )
    return summary, len(listing.invalid)


@router.get("")
def list_projects(request: Request) -> list[ProjectSummary]:
    return [
        _summary(request, path.name)[0] for path in list_workspaces(settings(request).projects_dir)
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(body: CreateProject, request: Request) -> ProjectCreated:
    projects_dir, repo = settings(request).projects_dir, Path(body.repo)
    result: InitResult
    with service_errors():
        try:
            if body.template is None:
                if body.template_ref is not None:
                    raise ApiError(
                        422, "validation_error", "template_ref needs template", field="template_ref"
                    )
                result = init_project(
                    body.name,
                    repo,
                    projects_dir=projects_dir,
                    branch=body.branch,
                    remote=body.remote,
                )
            else:
                result = init_from_template(
                    body.name,
                    repo,
                    body.template,
                    ref=body.template_ref,
                    projects_dir=projects_dir,
                    branch=body.branch,
                    remote=body.remote,
                )
        except TemplateError as exc:
            raise ApiError(409, "template_error", str(exc)) from exc
    return ProjectCreated(
        name=result.project.name, path=str(result.path), missing_notes=result.missing_notes
    )


@router.get("/{name}")
def get_project(name: ProjectName, request: Request) -> ProjectDetail:
    workspace(request, name)
    summary, invalid = _summary(request, name)
    with service_errors():
        project = load_project(name, projects_dir=settings(request).projects_dir)
    return ProjectDetail(
        **summary.model_dump(),
        repo=str(project.repo),
        default_branch=project.default_branch,
        remote=project.git.remote,
        invalid_tickets=invalid,
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
