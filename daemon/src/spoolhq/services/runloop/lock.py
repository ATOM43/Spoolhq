"""One run per project: ``<workspace>/.spoolhq/run.lock``.

The same OS lock as the daemon's single-instance lock (``core/daemon_lock.py``), held
by the worker thread while it works. The run loop also checks its own record of active
runs, which names the ticket and run, and covers a paused run that holds no thread.
"""

from pathlib import Path

from spoolhq.core.daemon_lock import DaemonLock, LockHeld, acquire_lock, holder
from spoolhq.services.runloop.model import RunActiveError

RUN_LOCK = ".spoolhq/run.lock"


def active_message(project: str, detail: str) -> str:
    return f"a run is already active in '{project}' ({detail})"


def take_run_lock(workspace: Path, project: str) -> DaemonLock:
    """Take the project's run lock; RunActiveError if another holder has it."""
    try:
        return acquire_lock(workspace / RUN_LOCK)
    except LockHeld as exc:
        raise RunActiveError(active_message(project, holder(exc.pid))) from None
