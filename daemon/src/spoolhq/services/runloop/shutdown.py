"""Cancelling every active run before the daemon exits (``POST /api/shutdown``)."""

from collections.abc import Iterable

from spoolhq.services.runloop.loop import RunLoop
from spoolhq.services.runloop.model import RunLoopError
from spoolhq.services.runs import Run

CANCEL_WAIT_S = 10.0
"""How long each run's worker gets to stop its agent and remove the worktree; the app
force-kills the daemon 15 s after asking."""


def cancel_all(loop: RunLoop, projects: Iterable[str], wait_s: float = CANCEL_WAIT_S) -> list[Run]:
    """Cancel each project's active run like Cancel does (run ``cancelled``, worktree
    removed, ticket back to ``ready``) and wait for its worker to finish."""
    cancelled = []
    for project in projects:
        try:
            if not loop.current(project).active:
                continue
            loop.cancel(project)
        except RunLoopError:
            continue  # a broken or vanished project has no run to cancel
        loop.wait(project, wait_s)
        run = loop.current(project).run
        if run is not None:
            cancelled.append(run)
    return cancelled
