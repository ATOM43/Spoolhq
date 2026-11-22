"""``POST /api/shutdown``: cancel every active run, then stop the daemon (token required).

The desktop app calls it when it quits a daemon it started."""

from collections.abc import Callable

from fastapi import APIRouter, Request, Security

from spoolhq.api.schemas.runs import RunView, Shutdown
from spoolhq.api.security import bearer_scheme
from spoolhq.services.runloop import RunLoop, cancel_all
from spoolhq.services.runs import RunRegistry

router = APIRouter(prefix="/api", dependencies=[Security(bearer_scheme)])


@router.post("/shutdown")
def shutdown(request: Request) -> Shutdown:
    """Cancel each active run like Cancel does (``cancelled``, worktree removed, ticket
    back to Ready), then close the event streams and exit once this answer is sent."""
    loop: RunLoop = request.app.state.runloop
    registry: RunRegistry = request.app.state.runs
    cancelled = cancel_all(loop, registry.projects)
    request_exit: Callable[[], None] | None = request.app.state.request_exit
    if request_exit is not None:
        request_exit()
    return Shutdown(cancelled=[RunView.of(run) for run in cancelled])
