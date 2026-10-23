"""Automatic resume after a usage limit: a timer driven by the run loop's clock.

A run paused by a usage limit resumes at ``reset_at`` plus ``RESUME_DELAY``. The timer
checks the injected clock once per ``poll_s`` on its own daemon thread, so tests can
advance a fake clock and call ``check()``. It is cancelled when the daemon shuts down.
Nothing resumes automatically after a crash: an interrupted run waits for
``spool run resume``.
"""

import logging
import threading
from collections.abc import Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

RESUME_DELAY = timedelta(seconds=60)


class ResumeTimer:
    """Calls ``on_due(project)`` once the clock reaches the time scheduled for it."""

    def __init__(
        self,
        clock: Callable[[], datetime],
        on_due: Callable[[str], None],
        *,
        poll_s: float = 1.0,
    ) -> None:
        self._clock = clock
        self._on_due = on_due
        self._poll_s = poll_s
        self._due: dict[str, datetime] = {}
        self._lock = threading.Lock()
        self._closed = threading.Event()
        self._thread: threading.Thread | None = None

    def schedule(self, project: str, reset_at: datetime) -> datetime:
        """Resume ``project`` at ``reset_at`` + 60 s; returns that time."""
        at = reset_at + RESUME_DELAY
        with self._lock:
            self._due[project] = at
            if self._thread is None and not self._closed.is_set():
                self._thread = threading.Thread(
                    target=self._poll, name="spoolhq-resume-timer", daemon=True
                )
                self._thread.start()
        return at

    def cancel(self, project: str) -> None:
        with self._lock:
            self._due.pop(project, None)

    def due_at(self, project: str) -> datetime | None:
        with self._lock:
            return self._due.get(project)

    def check(self) -> list[str]:
        """Fire every project whose time has come; returns them."""
        now = self._clock()
        with self._lock:
            fired = [project for project, at in self._due.items() if now >= at]
            for project in fired:
                del self._due[project]
        for project in fired:
            try:
                self._on_due(project)
            except Exception:
                logger.exception("automatic resume failed", extra={"project": project})
        return fired

    def _poll(self) -> None:
        while not self._closed.wait(self._poll_s):
            self.check()

    def close(self) -> None:
        self._closed.set()
        with self._lock:
            self._due.clear()
            thread = self._thread
        if thread is not None:
            thread.join(timeout=5)
