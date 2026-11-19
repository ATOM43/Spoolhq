"""Drafting tickets on the daemon: ``draft_tickets`` in a worker thread, as a job kept in
memory for an hour after it ends (like creation jobs, DECISIONS 337), recorded in the run
log as a run of kind ``draft`` with its usage. Nothing is written to ``tickets/``.

A job refuses to start, with a reason the form shows, when the planner's agent isn't
ready, a run is going in the project, or its plan is being generated.
"""

import copy
import logging
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from spoolhq.services.agents import AgentRunner, Outcome
from spoolhq.services.planner import Draft, DraftResult, PlannerError, draft_tickets
from spoolhq.services.projects import NO_TEST_COMMAND, Project, load_project, project_dir
from spoolhq.services.runloop.loop import RunLoop
from spoolhq.services.runloop.model import NotFoundError, RunActiveError, RunLoopError, user_errors
from spoolhq.services.runloop.planning import PlanJobs
from spoolhq.services.runloop.prompting import planner_code_map
from spoolhq.services.runs import (
    Attempt,
    AttemptKind,
    AttemptStatus,
    RunKind,
    RunLog,
    RunRegistry,
    RunStatus,
    append_transcript,
)

logger = logging.getLogger(__name__)

KEEP_S = 3600.0
CANCEL_WAIT_S = 15.0
SHUTDOWN_WAIT_S = 20.0


class AgentNotReadyError(RunLoopError):
    """The planner's backend can't run now."""

    code = "agent_unavailable"


@dataclass
class DraftJob:
    id: str
    project: str
    run_id: int
    state: Literal["running", "succeeded", "failed", "cancelled"] = "running"
    error: str | None = None
    drafts: tuple[Draft, ...] = ()
    ended_at: float | None = None


class DraftJobs:
    """Starts, reads and cancels the daemon's draft jobs."""

    def __init__(
        self,
        registry: RunRegistry,
        *,
        projects_dir: Path,
        home: Path,
        loop: RunLoop,
        plans: PlanJobs,
        runner: AgentRunner | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Without ``runner``, each project's ``agents.planner`` backend is used."""
        self._registry = registry
        self.projects_dir, self.home = projects_dir, home
        self._loop, self._plans, self.runner = loop, plans, runner
        self._clock = clock
        self._lock = threading.Lock()
        self._jobs: dict[str, tuple[DraftJob, threading.Event, threading.Thread]] = {}

    def start(self, project: str, request: str) -> DraftJob:
        """Start drafting tickets for ``request``; RunLoopError with the reason if it can't."""
        workspace = project_dir(project, self.projects_dir) if project else Path()
        if not project or not workspace.is_dir():
            raise NotFoundError(f"no project '{project}'")
        with user_errors():
            settings = load_project(project, projects_dir=self.projects_dir)
        if settings.commands.test is None:
            raise RunLoopError(NO_TEST_COMMAND)
        runner = self.runner or settings.agents.runner_for("planner")
        info = runner.detect()
        if not info.usable:
            reason = info.reason or f"{info.name} can't run"
            raise AgentNotReadyError(f"No agent is ready to draft tickets: {reason}")
        with self._loop._mutex:
            self._loop._check_free(project)
        if self._plans.planning(project):
            raise RunActiveError(f"a plan is being generated for '{project}'")
        with self._lock:
            self._prune()
            run_log = self._registry.open(workspace).run_log
            run = run_log.start_plan_run(RunKind.DRAFT)
            attempt = run_log.start_attempt(run.id, AttemptKind.DRAFT, backend=runner.name)
            job = DraftJob(id=uuid.uuid4().hex, project=project, run_id=run.id)
            cancel = threading.Event()
            thread = threading.Thread(
                target=self._work,
                args=(job, request, settings, runner, run_log, attempt, cancel),
                name=f"draft-{job.id}",
                daemon=True,
            )
            self._jobs[job.id] = (job, cancel, thread)
            thread.start()
            return copy.deepcopy(job)

    def _work(
        self,
        job: DraftJob,
        request: str,
        settings: Project,
        runner: AgentRunner,
        run_log: RunLog,
        attempt: Attempt,
        cancel: threading.Event,
    ) -> None:
        result: DraftResult | None = None

        def on_raw(message: dict[str, Any]) -> None:
            append_transcript(attempt, message)

        try:
            workspace = project_dir(job.project, self.projects_dir)
            result = draft_tickets(
                job.project,
                request,
                runner,
                projects_dir=self.projects_dir,
                home=self.home,
                cancel=cancel,
                on_raw=on_raw,
                code_map=planner_code_map(settings, workspace),
            )
            error = result.error
        except Exception as exc:
            logger.exception("drafting failed", extra={"project": job.project})
            error = str(exc) if isinstance(exc, PlannerError) else f"internal error: {exc}"
        cancelled = result is not None and result.outcome is Outcome.CANCELLED
        with self._lock:
            job.state = "cancelled" if cancelled else "failed" if error else "succeeded"
            job.error = None if cancelled else error
            job.drafts = result.drafts if result is not None else ()
            job.ended_at = self._clock()
        try:
            self._record(run_log, attempt, result, job)
        except Exception:
            logger.exception("cannot record the draft run", extra={"project": job.project})

    @staticmethod
    def _record(
        run_log: RunLog, attempt: Attempt, result: DraftResult | None, job: DraftJob
    ) -> None:
        if result is not None:
            run_log.record_usage(
                attempt.id,
                result.input_tokens,
                result.output_tokens,
                result.cost_micro_usd,
                result.cache_read_tokens,
            )
        reason: str | None
        if job.state == "succeeded":
            reason = f"{len(job.drafts)} draft tickets"
            statuses = (AttemptStatus.APPROVED, RunStatus.DONE)
        elif job.state == "cancelled":
            reason, statuses = "cancelled", (AttemptStatus.CANCELLED, RunStatus.CANCELLED)
        else:
            reason, statuses = job.error, (AttemptStatus.ERROR, RunStatus.BLOCKED)
        run_log.finish_attempt(attempt.id, statuses[0])
        run_log.set_run_status(attempt.run_id, statuses[1], reason)

    def _prune(self) -> None:
        now = self._clock()
        for job_id, (job, _, _) in list(self._jobs.items()):
            if job.ended_at is not None and now - job.ended_at > KEEP_S:
                del self._jobs[job_id]

    def _find(
        self, project: str, job_id: str
    ) -> tuple[DraftJob, threading.Event, threading.Thread]:
        self._prune()
        found = self._jobs.get(job_id)
        if found is None or found[0].project != project:
            raise NotFoundError(f"no draft job {job_id!r} in '{project}'")
        return found

    def get(self, project: str, job_id: str) -> DraftJob:
        """A copy of the job as it is now."""
        with self._lock:
            return copy.deepcopy(self._find(project, job_id)[0])

    def wait(self, project: str, job_id: str, timeout: float | None = None) -> DraftJob:
        with self._lock:
            thread = self._find(project, job_id)[2]
        thread.join(timeout)
        return self.get(project, job_id)

    def cancel(self, project: str, job_id: str) -> DraftJob:
        """Stop the agent and wait (up to 15 s) for the job to end; an ended job stays."""
        with self._lock:
            self._find(project, job_id)[1].set()
        return self.wait(project, job_id, CANCEL_WAIT_S)

    def close(self) -> None:
        """Daemon shutdown: stop the agents and wait for their threads."""
        with self._lock:
            jobs = list(self._jobs.values())
        for _, cancel, _ in jobs:
            cancel.set()
        for _, _, thread in jobs:
            thread.join(SHUTDOWN_WAIT_S)
