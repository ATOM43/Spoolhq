"""The daemon's run logs: one ``RunLog`` and one ``EventBus`` per workspace."""

import logging
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path

from spoolhq.services.projects import list_workspaces
from spoolhq.services.runs.bus import EventBus
from spoolhq.services.runs.db import Clock, RunLogError, state_db_path, utc_now
from spoolhq.services.runs.log import RunLog
from spoolhq.services.runs.recovery import recover_interrupted

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkspaceRuns:
    project: str
    run_log: RunLog
    bus: EventBus


class RunRegistry:
    """Open run logs by project name. ``close`` closes them all."""

    def __init__(self, daemon_instance: str, clock: Clock = utc_now) -> None:
        self.daemon_instance = daemon_instance
        self._clock = clock
        self._workspaces: dict[str, WorkspaceRuns] = {}
        self._lock = threading.Lock()

    @classmethod
    def start(
        cls, projects_dir: Path, *, daemon_instance: str, clock: Clock = utc_now
    ) -> "RunRegistry":
        """Open every workspace's run log and recover runs a previous daemon left active.

        A workspace whose ``state.db`` cannot be opened is logged as an error and
        skipped. Call this only while holding the daemon single-instance lock.
        """
        registry = cls(daemon_instance, clock)
        try:
            for workspace in list_workspaces(projects_dir):
                registry._open(workspace, clock)
        except BaseException:
            registry.close()
            raise
        return registry

    def _open(self, workspace: Path, clock: Clock) -> None:
        project = workspace.name
        bus = EventBus()
        try:
            run_log = RunLog(workspace, bus=bus, clock=clock, daemon_instance=self.daemon_instance)
        except (RunLogError, sqlite3.Error, OSError) as exc:
            logger.error(
                "cannot open the run log; skipping this project",
                extra={
                    "project": project,
                    "path": str(state_db_path(workspace)),
                    "error": str(exc),
                },
            )
            return
        try:
            bus.start_at(run_log.last_event_id())
            recovered = recover_interrupted(run_log)
        except (sqlite3.Error, OSError) as exc:
            run_log.close()
            logger.error(
                "cannot recover interrupted runs; skipping this project",
                extra={
                    "project": project,
                    "path": str(state_db_path(workspace)),
                    "error": str(exc),
                },
            )
            return
        for run in recovered:
            logger.warning(
                "run interrupted by a daemon restart",
                extra={
                    "project": project,
                    "run_id": run.id,
                    "ticket_id": run.ticket_id,
                    "status": run.status.value,
                },
            )
        self._workspaces[project] = WorkspaceRuns(project=project, run_log=run_log, bus=bus)

    def open(self, workspace: Path) -> WorkspaceRuns:
        """The workspace's run log, opened (and recovered) now if the project was created
        after the daemon started. Raises RunLogError if it can't be opened."""
        with self._lock:
            if workspace.name not in self._workspaces:
                self._open(workspace, self._clock)
            try:
                return self._workspaces[workspace.name]
            except KeyError:
                raise RunLogError(f"cannot open the run log of {workspace.name!r}") from None

    @property
    def projects(self) -> list[str]:
        return sorted(self._workspaces)

    def get(self, project: str) -> WorkspaceRuns:
        try:
            return self._workspaces[project]
        except KeyError:
            raise KeyError(f"no run log for project {project!r}") from None

    def close(self) -> None:
        workspaces, self._workspaces = self._workspaces, {}
        for entry in workspaces.values():
            entry.run_log.close()
