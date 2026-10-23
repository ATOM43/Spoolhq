"""Run endpoints: start, pause, resume and cancel a project's run, discard a ticket's
leftover worktree, and read the current run (token required). Thin: the work is
``services.runloop.RunLoop``'s; the full REST and WebSocket API comes in T19.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, HTTPException, Request, Security, status

from spoolhq.api.schemas.runs import CurrentRun, Discarded, RunView, StartRun
from spoolhq.api.security import bearer_scheme
from spoolhq.services.runloop import NotFoundError, RunLoop, RunLoopError

router = APIRouter(prefix="/api/projects/{name}", dependencies=[Security(bearer_scheme)])


def _loop(request: Request) -> RunLoop:
    loop: RunLoop = request.app.state.runloop
    return loop


@contextmanager
def _errors() -> Iterator[None]:
    """Unknown project, run or ticket → 404; any other refusal → 409, with the message."""
    try:
        yield
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except RunLoopError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/runs", status_code=status.HTTP_201_CREATED)
def start_run(name: str, body: StartRun, request: Request) -> RunView:
    with _errors():
        return RunView.of(_loop(request).start(name, body.mode, body.ticket))


@router.post("/runs/{run_id}/pause")
def pause_run(name: str, run_id: int, request: Request) -> RunView:
    with _errors():
        return RunView.of(_loop(request).pause(name, run_id))


@router.post("/runs/{run_id}/resume")
def resume_run(name: str, run_id: int, request: Request) -> RunView:
    with _errors():
        return RunView.of(_loop(request).resume(name, run_id))


@router.post("/runs/{run_id}/cancel")
def cancel_run(name: str, run_id: int, request: Request) -> RunView:
    with _errors():
        return RunView.of(_loop(request).cancel(name, run_id))


@router.post("/tickets/{ticket_id}/discard")
def discard_ticket(name: str, ticket_id: str, request: Request) -> Discarded:
    with _errors():
        _loop(request).discard(name, ticket_id)
    return Discarded(ticket_id=ticket_id)


@router.get("/runs/current")
def current_run(name: str, request: Request) -> CurrentRun:
    with _errors():
        return CurrentRun.of(_loop(request).current(name))
