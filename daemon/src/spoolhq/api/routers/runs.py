"""Run endpoints: start (next, all, one ticket), pause, resume and cancel a project's run,
approve (or integrate) or reject a ticket waiting for a person, discard a ticket's
leftover worktree, read the current run, the paged run history, one run with its
attempts, its stored events and an attempt's files (token required). Thin: the work is
``services.runloop.RunLoop``'s and ``services.runs``'.
"""

import json
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Query, Request, Security, status
from fastapi.responses import FileResponse

from spoolhq.api.errors import ApiError, service_errors
from spoolhq.api.params import ProjectName, TicketId, run_log, workspace
from spoolhq.api.schemas.events import EventEnvelope, EventList
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
from spoolhq.services.runloop import (
    DiffReport,
    GatesReport,
    ReviewReport,
    RunLoop,
    diff_report,
    gates_report,
    review_report,
)
from spoolhq.services.runs import ArtifactName, attempt_dir, page_events, page_runs

router = APIRouter(prefix="/api/projects/{name}", dependencies=[Security(bearer_scheme)])
RunIdQuery = Annotated[
    int | None, Query(description="The run to act on (default: the project's current run).")
]


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


EVENTS_LIMIT = 2000


@router.get("/runs/{run_id}/events")
def list_events(
    name: ProjectName,
    run_id: int,
    request: Request,
    attempt: Annotated[int | None, Query(ge=1)] = None,
    after: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1)] = 500,
) -> EventList:
    """A run's stored events after ``after``, oldest first, as the event stream sends
    them; with ``attempt``, from that attempt's start until the next one's. Pass
    ``next_after`` back as ``after`` for the next page."""
    if limit > EVENTS_LIMIT:
        raise ApiError(400, "limit_too_large", f"limit is at most {EVENTS_LIMIT}", field="limit")
    log = run_log(request, name)
    try:
        run, attempts = log.get_run(run_id), log.list_attempts(run_id)
        page = page_events(log, run_id, attempt, after, limit)
    except (KeyError, StopIteration) as exc:
        raise ApiError(404, "not_found", f"no such run or attempt in {name!r}") from exc
    numbers = {a.id: a.number for a in attempts}
    items = [
        EventEnvelope.of(e, run.ticket_id, numbers.get(e.attempt_id) if e.attempt_id else None)
        for e in page.events
    ]
    return EventList(items=items, next_after=page.next_after)


def _artifact(request: Request, name: str, run_id: int, number: int, file: ArtifactName) -> Path:
    """The attempt's file: 404 ``not_found`` for an unknown run or attempt, 404
    ``not_ready`` while its step hasn't written it."""
    log = run_log(request, name)
    try:
        attempt = next(a for a in log.list_attempts(run_id) if a.number == number)
        folder = attempt_dir(workspace(request, name), attempt)
    except (KeyError, StopIteration, ValueError) as exc:
        raise ApiError(404, "not_found", f"run {run_id} has no attempt {number}") from exc
    path = folder / file.value
    # Never follow a link out of the attempt folder.
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(folder):
        raise ApiError(404, "not_ready", f"attempt {number} has no {file.value} yet")
    return path


def _json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


@router.get(
    "/runs/{run_id}/attempts/{number}/transcript",
    response_class=FileResponse,
    responses={200: {"content": {"application/x-ndjson": {}}}},
)
def get_transcript(name: ProjectName, run_id: int, number: int, request: Request) -> FileResponse:
    """The attempt's raw agent streams (``transcript.jsonl``), as stored."""
    path = _artifact(request, name, run_id, number, ArtifactName.TRANSCRIPT)
    return FileResponse(path, media_type="application/x-ndjson")


@router.get("/runs/{run_id}/attempts/{number}/gates")
def get_gates(name: ProjectName, run_id: int, number: int, request: Request) -> GatesReport:
    """Each gate's state, duration and trimmed output, with its first failure line."""
    return gates_report(_json(_artifact(request, name, run_id, number, ArtifactName.GATES)))


@router.get("/runs/{run_id}/attempts/{number}/review")
def get_review(name: ProjectName, run_id: int, number: int, request: Request) -> ReviewReport:
    """The reviewer's verdict, summary and each "Done when" item, in the ticket's order."""
    return review_report(_json(_artifact(request, name, run_id, number, ArtifactName.REVIEW)))


@router.get("/runs/{run_id}/attempts/{number}/diff")
def get_diff(name: ProjectName, run_id: int, number: int, request: Request) -> DiffReport:
    """The attempt's committed diff by file; a patch over 2,000 lines is cut."""
    path = _artifact(request, name, run_id, number, ArtifactName.DIFF)
    # Bytes, so a CRLF file's \r survives (read_text would translate newlines).
    return diff_report(path.read_bytes().decode("utf-8", errors="replace"))
