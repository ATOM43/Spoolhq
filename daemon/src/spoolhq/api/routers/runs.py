"""Run endpoints: start (next, all, one ticket), pause, resume and cancel a project's run,
approve (or integrate) or reject a ticket waiting for a person, discard a ticket's
leftover worktree, read the current run, the paged run history, one run with its
attempts and an attempt's files (token required). Thin: the work is
``services.runloop.RunLoop``'s and ``services.runs``'.
"""

from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Query, Request, Security, status
from fastapi.responses import FileResponse

from spoolhq.api.errors import ApiError, service_errors
from spoolhq.api.params import ProjectName, TicketId, run_log, workspace
from spoolhq.api.schemas.runs import (
    AttemptView,
    CurrentRun,
    Discarded,
    Reject,
    RunDetail,
    RunList,
    RunView,
)
from spoolhq.api.security import bearer_scheme
from spoolhq.services.runloop import RunLoop
from spoolhq.services.runs import ArtifactName, attempt_dir, page_runs

router = APIRouter(prefix="/api/projects/{name}", dependencies=[Security(bearer_scheme)])
RunIdQuery = Annotated[
    int | None, Query(description="The run to act on (default: the project's current run).")
]


class Artifact(StrEnum):
    TRANSCRIPT = "transcript"
    GATES = "gates"
    DIFF = "diff"
    REVIEW = "review"


ARTIFACT_FILES = {
    Artifact.TRANSCRIPT: (ArtifactName.TRANSCRIPT, "application/x-ndjson"),
    Artifact.GATES: (ArtifactName.GATES, "application/json"),
    Artifact.DIFF: (ArtifactName.DIFF, "text/x-diff; charset=utf-8"),
    Artifact.REVIEW: (ArtifactName.REVIEW, "application/json"),
}


def _loop(request: Request) -> RunLoop:
    loop: RunLoop = request.app.state.runloop
    return loop


@router.post("/run/next", status_code=status.HTTP_201_CREATED)
def run_next(name: ProjectName, request: Request) -> RunView:
    """Run the next ready ticket."""
    with service_errors():
        return RunView.of(_loop(request).start(name, "next"))


@router.post("/run/all", status_code=status.HTTP_201_CREATED)
def run_all(name: ProjectName, request: Request) -> RunView:
    """Run ready tickets one after another until one doesn't finish."""
    with service_errors():
        return RunView.of(_loop(request).start(name, "all"))


@router.post("/run/ticket/{ticket_id}", status_code=status.HTTP_201_CREATED)
def run_ticket(name: ProjectName, ticket_id: TicketId, request: Request) -> RunView:
    """Run this ticket (it must be ready)."""
    with service_errors():
        return RunView.of(_loop(request).start(name, "next", ticket_id))


@router.post("/run/pause")
def pause_run(name: ProjectName, request: Request, run_id: RunIdQuery = None) -> RunView:
    with service_errors():
        return RunView.of(_loop(request).pause(name, run_id))


@router.post("/run/resume")
def resume_run(name: ProjectName, request: Request, run_id: RunIdQuery = None) -> RunView:
    with service_errors():
        return RunView.of(_loop(request).resume(name, run_id))


@router.post("/run/cancel")
def cancel_run(name: ProjectName, request: Request, run_id: RunIdQuery = None) -> RunView:
    with service_errors():
        return RunView.of(_loop(request).cancel(name, run_id))


@router.post("/tickets/{ticket_id}/approve")
@router.post("/tickets/{ticket_id}/integrate")
def approve_ticket(name: ProjectName, ticket_id: TicketId, request: Request) -> RunView:
    with service_errors():
        return RunView.of(_loop(request).approve(name, ticket_id))


@router.post("/tickets/{ticket_id}/reject")
def reject_ticket(
    name: ProjectName, ticket_id: TicketId, body: Reject, request: Request
) -> RunView:
    with service_errors():
        return RunView.of(_loop(request).reject(name, ticket_id, body.note))


@router.post("/tickets/{ticket_id}/discard")
def discard_ticket(name: ProjectName, ticket_id: TicketId, request: Request) -> Discarded:
    with service_errors():
        _loop(request).discard(name, ticket_id)
    return Discarded(ticket_id=ticket_id)


@router.get("/runs/current")
def current_run(name: ProjectName, request: Request) -> CurrentRun:
    latest = run_log(request, name).last_event_id()  # first, so nothing falls between
    with service_errors():
        return CurrentRun.of(_loop(request).current(name), latest)


@router.get("/runs")
def list_runs(
    name: ProjectName,
    request: Request,
    cursor: Annotated[str | None, Query(max_length=200)] = None,
    limit: Annotated[int, Query(ge=1)] = 50,
) -> RunList:
    """Runs, newest first, a page at a time; pass ``next_cursor`` back as ``cursor``."""
    if limit > 200:
        raise ApiError(400, "limit_too_large", "limit is at most 200", field="limit")
    try:
        return RunList.of(page_runs(run_log(request, name), cursor, limit))
    except ValueError as exc:
        raise ApiError(400, "invalid_cursor", str(exc), field="cursor") from exc


@router.get("/runs/{run_id}")
def get_run(name: ProjectName, run_id: int, request: Request) -> RunDetail:
    log = run_log(request, name)
    try:
        run, attempts = log.get_run(run_id), log.list_attempts(run_id)
    except KeyError as exc:
        raise ApiError(404, "not_found", f"no run {run_id} in {name!r}") from exc
    return RunDetail(**RunView.of(run).model_dump(), attempts=[AttemptView.of(a) for a in attempts])


@router.get(
    "/runs/{run_id}/attempts/{number}/{artifact}",
    response_class=FileResponse,
    responses={200: {"content": {"application/octet-stream": {}}}},
)
def get_artifact(
    name: ProjectName, run_id: int, number: int, artifact: Artifact, request: Request
) -> FileResponse:
    """One file of an attempt, as stored; 404 if the attempt has none."""
    log = run_log(request, name)
    missing = ApiError(404, "not_found", f"run {run_id} has no {artifact} for attempt {number}")
    try:
        attempt = next(a for a in log.list_attempts(run_id) if a.number == number)
        folder = attempt_dir(workspace(request, name), attempt)
    except (KeyError, StopIteration, ValueError) as exc:
        raise missing from exc
    file_name, media_type = ARTIFACT_FILES[artifact]
    path = folder / file_name.value
    # Never follow a link out of the attempt folder.
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(folder):
        raise missing
    return FileResponse(path, media_type=media_type)
