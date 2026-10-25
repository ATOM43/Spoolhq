"""Plan generation on the daemon: ``generate_plan`` in a worker thread, recorded in the
run log as a run of kind ``plan`` with one attempt and its usage.

The checks that need no agent (the project, ``CONTEXT.md``, valid ticket files) run
before the run starts, so the caller gets those errors at once; one plan per project
runs at a time.
"""

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from spoolhq.services.agents import AgentRunner, Outcome
from spoolhq.services.planner import (
    PlannerError,
    PlanResult,
    approve_plan,
    generate_plan,
    load_existing,
    read_spec,
)
from spoolhq.services.projects import load_project, project_dir
from spoolhq.services.runloop.model import NotFoundError, RunActiveError, RunLoopError, user_errors
from spoolhq.services.runs import (
    Attempt,
    AttemptKind,
    AttemptStatus,
    Run,
    RunLog,
    RunRegistry,
    RunStatus,
    append_transcript,
)

logger = logging.getLogger(__name__)

SHUTDOWN_WAIT_S = 20.0


@dataclass
class _Job:
    run_id: int
    thread: threading.Thread
    cancel: threading.Event


class PlanJobs:
    """Starts plan generation for the daemon's projects and approves plans."""

    def __init__(
        self, registry: RunRegistry, *, projects_dir: Path, home: Path, runner: AgentRunner
    ) -> None:
        self._registry = registry
        self.projects_dir = projects_dir
        self.home = home
        self.runner = runner
        self._mutex = threading.Lock()
        self._jobs: dict[str, _Job] = {}

    def _workspace(self, project: str) -> Path:
        workspace = project_dir(project, self.projects_dir) if project else Path()
        if not project or not workspace.is_dir():
            raise NotFoundError(f"no project '{project}'")
        return workspace

    def start(self, project: str, template_description: str | None = None) -> Run:
        """Start generating ``project``'s plan; returns the ``plan`` run (``running``)."""
        workspace = self._workspace(project)
        with user_errors():
            load_project(project, projects_dir=self.projects_dir)
        try:
            read_spec(workspace)
            load_existing(project, projects_dir=self.projects_dir)
        except PlannerError as exc:
            raise RunLoopError(str(exc)) from exc
        with self._mutex:
            job = self._jobs.get(project)
            if job is not None and job.thread.is_alive():
                raise RunActiveError(
                    f"a plan is already being generated for '{project}' (run {job.run_id})"
                )
            run_log = self._registry.open(workspace).run_log
            run = run_log.start_plan_run()
            attempt = run_log.start_attempt(run.id, AttemptKind.PLAN, backend=self.runner.name)
            cancel = threading.Event()
            thread = threading.Thread(
                target=self._work,
                args=(project, run_log, attempt, template_description, cancel),
                name=f"plan-{project}",
                daemon=True,
            )
            self._jobs[project] = _Job(run.id, thread, cancel)
            thread.start()
        return run

    def _work(
        self,
        project: str,
        run_log: RunLog,
        attempt: Attempt,
        template_description: str | None,
        cancel: threading.Event,
    ) -> None:
        result: PlanResult | None = None

        def on_raw(message: dict[str, Any]) -> None:
            append_transcript(attempt, message)

        try:
            result = generate_plan(
                project,
                self.runner,
                projects_dir=self.projects_dir,
                home=self.home,
                template_description=template_description,
                on_raw=on_raw,
                cancel=cancel,
            )
            error = result.error
        except Exception as exc:
            logger.exception("plan generation failed", extra={"project": project})
            error = str(exc) if isinstance(exc, PlannerError) else f"internal error: {exc}"
        try:
            self._record(run_log, attempt, result, error)
        except Exception:
            logger.exception("cannot record the plan run", extra={"project": project})

    @staticmethod
    def _record(
        run_log: RunLog, attempt: Attempt, result: PlanResult | None, error: str | None
    ) -> None:
        if result is not None:
            run_log.record_usage(
                attempt.id,
                result.input_tokens,
                result.output_tokens,
                result.cost_micro_usd,
                result.cache_read_tokens,
            )
        cancelled = result is not None and result.outcome is Outcome.CANCELLED
        reason: str | None
        if error is None and result is not None:
            reason = f"{len(result.written)} draft tickets written"
            statuses = (AttemptStatus.APPROVED, RunStatus.DONE)
        elif cancelled:
            reason, statuses = "cancelled", (AttemptStatus.CANCELLED, RunStatus.CANCELLED)
        else:
            reason, statuses = error, (AttemptStatus.ERROR, RunStatus.BLOCKED)
        run_log.finish_attempt(attempt.id, statuses[0])
        run_log.set_run_status(attempt.run_id, statuses[1], reason)

    def approve(self, project: str) -> tuple[str, ...]:
        """Move every draft of ``project`` to ``ready``; RunLoopError lists the problems."""
        self._workspace(project)
        try:
            return approve_plan(project, projects_dir=self.projects_dir)
        except PlannerError as exc:
            raise RunLoopError(str(exc)) from exc

    def wait(self, project: str, timeout: float | None = None) -> None:
        """Wait for the project's plan thread to finish (tests, shutdown)."""
        with self._mutex:
            job = self._jobs.get(project)
        if job is not None:
            job.thread.join(timeout)

    def close(self) -> None:
        """Daemon shutdown: cancel the planners and wait for their threads."""
        with self._mutex:
            jobs = list(self._jobs.values())
        for job in jobs:
            job.cancel.set()
        for job in jobs:
            job.thread.join(SHUTDOWN_WAIT_S)
