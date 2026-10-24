"""``RunLoop``: the daemon's runs, one worker thread per active run.

The daemon owns the loop, so a run survives the terminal that started it and can be
paused, resumed or cancelled from another one. One run per project at a time: the
loop's record of active runs (which also covers a paused run with no thread) plus the
project's ``run.lock``. Requests from other threads only set flags; the worker acts on
them between steps. See ``docs/run-loop.md``.
"""

import logging
import threading
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Literal

from spoolhq.services.gates import run_gates
from spoolhq.services.git import GitError, Worktree, WorktreeManager, ensure_clean
from spoolhq.services.git import ensure_no_operation_in_progress as ensure_no_operation
from spoolhq.services.projects import Project, load_project, project_dir
from spoolhq.services.runloop.integration import LocalIntegrator, last_merged
from spoolhq.services.runloop.integrator import HoldForIntegration, Integrator
from spoolhq.services.runloop.lock import active_message, take_run_lock
from spoolhq.services.runloop.machine import drive, next_kind
from spoolhq.services.runloop.model import (
    Active,
    Agents,
    Current,
    Ending,
    EndKind,
    Flags,
    GatesFn,
    NotFoundError,
    RunActiveError,
    RunContext,
    RunLoopError,
    record_phase,
    user_errors,
)
from spoolhq.services.runloop.resume import ResumeTimer
from spoolhq.services.runs import (
    AttemptKind,
    EventKind,
    Run,
    RunLog,
    RunRegistry,
    RunStatus,
    format_ts,
    utc_now,
)
from spoolhq.services.scheduler import apply_transition, explain_idle, next_ready
from spoolhq.services.tickets import Ticket, list_tickets, load_ticket

logger = logging.getLogger(__name__)

Mode = Literal["next", "all"]
SHUTDOWN_WAIT_S = 20.0


class RunLoop:
    """Starts, pauses, resumes, cancels and discards runs of the daemon's projects."""

    def __init__(
        self,
        registry: RunRegistry,
        *,
        projects_dir: Path,
        worktrees_dir: Path,
        home: Path,
        agents: Agents,
        integrator: Integrator | None = None,
        clock: Callable[[], datetime] = utc_now,
        gates: GatesFn = run_gates,
        poll_s: float = 1.0,
    ) -> None:
        self._registry = registry
        self.projects_dir = projects_dir
        self.worktrees_dir = worktrees_dir
        self.home = home
        self.agents = agents
        self.integrator: Integrator = integrator or LocalIntegrator(clock=clock)
        self.gates = gates
        self._mutex = threading.RLock()
        self._active: dict[str, Active] = {}
        self.timer = ResumeTimer(clock, self._auto_resume, poll_s=poll_s)

    # --- helpers ----------------------------------------------------------------------

    def _project(self, project: str) -> tuple[Project, Path, RunLog]:
        workspace = project_dir(project, self.projects_dir) if project else Path()
        if not project or not workspace.is_dir():
            raise NotFoundError(f"no project '{project}'")
        with user_errors():
            settings = load_project(project, projects_dir=self.projects_dir)
        return settings, workspace, self._registry.open(workspace).run_log

    def _manager(self, settings: Project) -> WorktreeManager:
        return WorktreeManager(
            settings.repo_path, settings.name, settings.default_branch, self.worktrees_dir
        )

    def _ticket_status(self, project: str, ticket_id: str, status: str) -> None:
        apply_transition(project, ticket_id, status, projects_dir=self.projects_dir)

    def _check_free(self, project: str) -> None:
        active = self._active.get(project)
        if active is not None:
            detail = f"{active.ticket_id}, run {active.run_id}"
            raise RunActiveError(active_message(project, detail))

    def _context(
        self,
        settings: Project,
        workspace: Path,
        run_log: RunLog,
        ticket: Ticket,
        run: Run,
        manager: WorktreeManager,
        worktree: Worktree,
        integrator: Integrator | None = None,
    ) -> RunContext:
        if integrator is None:
            hold = settings.run.integration == "hold"
            integrator = HoldForIntegration() if hold else self.integrator
        return RunContext(
            project=settings,
            workspace=workspace,
            projects_dir=self.projects_dir,
            home=self.home,
            ticket=ticket,
            run=run,
            run_log=run_log,
            worktrees=manager,
            worktree=worktree,
            agents=self.agents,
            integrator=integrator,
            gates=self.gates,
            flags=Flags(),
        )

    def _pick(self, project: str, ticket_id: str | None) -> Ticket | None:
        listing = list_tickets(project, projects_dir=self.projects_dir)
        if ticket_id is None:
            return next_ready(listing.tickets)
        ticket = next((t for t in listing.tickets if t.id == ticket_id), None)
        if ticket is None:
            raise NotFoundError(f"ticket {ticket_id} not found in '{project}'")
        if ticket.meta.status != "ready":
            raise RunLoopError(f"{ticket_id} is {ticket.meta.status}, not ready")
        return ticket

    def _begin(
        self, settings: Project, workspace: Path, run_log: RunLog, ticket: Ticket
    ) -> RunContext:
        """Ticket → running, a new run row and its worktree."""
        project, tid = settings.name, ticket.id
        self._ticket_status(project, tid, "running")
        run = run_log.start_run(tid)
        record_phase(run_log, run.id, "picked", f"{tid} · {ticket.meta.title} · run {run.id}")
        manager = self._manager(settings)
        try:
            worktree = manager.create(tid, ticket.meta.title, run.id)
        except (GitError, OSError) as exc:
            reason = f"cannot create the worktree: {exc}"
            record_phase(run_log, run.id, "blocked", f"{tid} · blocked · {reason}")
            run_log.set_run_status(run.id, RunStatus.BLOCKED, reason)
            self._ticket_status(project, tid, "blocked")
            raise RunLoopError(reason) from exc
        ctx = self._context(settings, workspace, run_log, ticket, run, manager, worktree)
        ctx.phase("worktree", f"{tid} · worktree · {worktree.path}")
        return ctx

    def _spawn(self, active: Active, ctx: RunContext, kind: AttemptKind | None, all_: bool) -> None:
        ctx.flags = active.flags
        active.thread = threading.Thread(
            target=self._work,
            args=(active, ctx, kind, all_),
            name=f"spoolhq-run-{ctx.project.name}",
            daemon=True,
        )
        active.thread.start()

    # --- the worker -------------------------------------------------------------------

    def _work(self, active: Active, ctx: RunContext, kind: AttemptKind | None, all_: bool) -> None:
        ending = Ending(EndKind.STOPPED)
        try:
            while True:
                try:
                    ending = drive(ctx, kind)
                except Exception as exc:
                    logger.exception("the run failed", extra={"run_id": ctx.run.id})
                    ending = Ending(EndKind.BLOCKED, f"internal error: {exc}")
                self._end(ctx, ending)
                if not all_ or ending.kind is not EndKind.DONE or active.flags.stop.is_set():
                    break
                with user_errors():
                    ticket = self._pick(ctx.project.name, None)
                    if ticket is None:
                        break
                    ctx = self._begin(ctx.project, ctx.workspace, ctx.run_log, ticket)
                ctx.flags = active.flags
                with self._mutex:
                    active.ticket_id, active.run_id = ticket.id, ctx.run.id
                kind = AttemptKind.INITIAL
        except Exception:
            logger.exception("the run loop failed", extra={"project": ctx.project.name})
        finally:
            self._release(ctx.project.name, active, keep=ending.kind is EndKind.PAUSED)

    def _end(self, ctx: RunContext, ending: Ending) -> None:
        """Record how the run ended and move the ticket and worktree to match."""
        tid, log, run_id, project = ctx.ticket_id, ctx.run_log, ctx.run.id, ctx.project.name
        kind = ending.kind
        try:
            if kind is EndKind.DONE:
                ctx.worktrees.teardown(ctx.worktree)
                self._ticket_status(project, tid, "done")
                if ctx.run.status is not RunStatus.DONE:  # the integrator may have closed it
                    ctx.run = log.set_run_status(run_id, RunStatus.DONE)
                ctx.phase("done", f"{tid} · done")
            elif kind is EndKind.HELD:
                self._ticket_status(project, tid, "awaiting_approval")
                ctx.run = log.set_run_status(run_id, RunStatus.AWAITING_APPROVAL, ending.reason)
            elif kind is EndKind.BLOCKED:
                ctx.phase("blocked", f"{tid} · blocked · {ending.reason}")
                ctx.run = log.set_run_status(run_id, RunStatus.BLOCKED, ending.reason)
                self._ticket_status(project, tid, "blocked")
            elif kind is EndKind.PAUSED:
                text = f"{tid} · paused · {ending.reason}"
                if ending.reset_at is not None:
                    at = self.timer.schedule(project, ending.reset_at)
                    text += f"; resumes at {format_ts(at)}"
                ctx.phase("paused", text)
                ctx.run = log.set_run_status(
                    run_id, RunStatus.PAUSED, ending.reason, reset_at=ending.reset_at
                )
            elif kind is EndKind.CANCELLED:
                ctx.worktrees.teardown(ctx.worktree)
                ctx.run = log.set_run_status(run_id, RunStatus.CANCELLED, "cancelled by the user")
                self._ticket_status(project, tid, "ready")
                ctx.phase("cancelled", f"{tid} · cancelled")
            # STOPPED: the daemon is shutting down; startup recovery marks it interrupted.
        except Exception:
            logger.exception("cannot record the end of the run", extra={"run_id": run_id})

    def _release(self, project: str, active: Active, *, keep: bool) -> None:
        with self._mutex:
            if active.lock is not None:
                active.lock.release()
                active.lock = None
            active.thread = None
            if not keep and self._active.get(project) is active:
                del self._active[project]

    def _auto_resume(self, project: str) -> None:
        try:
            self.resume(project)
        except RunLoopError as exc:
            logger.warning("cannot resume the run", extra={"project": project, "error": str(exc)})

    # --- requests ---------------------------------------------------------------------

    def start(self, project: str, mode: Mode = "next", ticket_id: str | None = None) -> Run:
        """Start a run of ``ticket_id`` or the next ready ticket (``all``: then the next…)."""
        settings, workspace, run_log = self._project(project)
        with self._mutex:
            self._check_free(project)
            lock = take_run_lock(workspace, project)
            try:
                with user_errors():
                    ticket = self._pick(project, ticket_id)
                    if ticket is None:
                        listing = list_tickets(project, projects_dir=self.projects_dir)
                        idle = explain_idle(listing.tickets)
                        reason = idle.message if idle is not None else "no ticket is ready"
                        raise RunLoopError(f"nothing to run in '{project}': {reason}")
                    ensure_no_operation(settings.repo_path)
                    ensure_clean(settings.repo_path)
                    ctx = self._begin(settings, workspace, run_log, ticket)
            except BaseException:
                lock.release()
                raise
            active = Active(ticket.id, ctx.run.id, Flags(), lock=lock)
            self._active[project] = active
            self._spawn(active, ctx, AttemptKind.INITIAL, mode == "all")
            return ctx.run

    def _get_active(self, project: str, run_id: int | None) -> Active:
        active = self._active.get(project)
        if active is None:
            raise RunLoopError(f"no active run in '{project}'")
        if run_id is not None and run_id != active.run_id:
            raise NotFoundError(f"run {run_id} is not the active run in '{project}'")
        return active

    def pause(self, project: str, run_id: int | None = None) -> Run:
        """Stop after the current step; the ticket stays running, the run ``paused``."""
        _, _, run_log = self._project(project)
        with self._mutex:
            active = self._get_active(project, run_id)
            if active.thread is None:
                raise RunLoopError(f"run {active.run_id} in '{project}' is already paused")
            active.flags.pause.set()
            return run_log.get_run(active.run_id)

    def cancel(self, project: str, run_id: int | None = None) -> Run:
        """Stop the agent, remove the worktree and its branch, ticket back to ``ready``."""
        settings, _, run_log = self._project(project)
        with self._mutex:
            active = self._get_active(project, run_id)
            if active.thread is not None:
                active.flags.cancel.set()  # the worker stops the agent and cleans up
                return run_log.get_run(active.run_id)
            # Paused: no worker, so clean up here.
            self.timer.cancel(project)
            del self._active[project]
            with user_errors():
                self._manager(settings).teardown(active.ticket_id)
                run = run_log.set_run_status(
                    active.run_id, RunStatus.CANCELLED, "cancelled by the user"
                )
                self._ticket_status(project, active.ticket_id, "ready")
            record_phase(run_log, run.id, "cancelled", f"{active.ticket_id} · cancelled")
            return run

    def _resumable(self, project: str, run_log: RunLog) -> Run | None:
        """The newest paused or interrupted run whose ticket is still running."""
        seen: set[str] = set()
        for run in run_log.list_runs(limit=200):
            if run.ticket_id in seen:
                continue
            seen.add(run.ticket_id)
            if run.status not in (RunStatus.PAUSED, RunStatus.INTERRUPTED):
                continue
            ticket = load_ticket(project, run.ticket_id, projects_dir=self.projects_dir)
            if ticket.meta.status == "running":
                return run
        return None

    def resume(self, project: str, run_id: int | None = None) -> Run:
        """Continue a paused run, or one a stopped daemon interrupted, in its worktree,
        with a new attempt of the kind that was cut off."""
        settings, workspace, run_log = self._project(project)
        with self._mutex:
            active = self._active.get(project)
            if active is not None and active.thread is not None:
                self._check_free(project)
            with user_errors():
                found = (
                    run_log.get_run(active.run_id)
                    if active is not None
                    else self._resumable(project, run_log)
                )
            if found is None:
                raise RunLoopError(f"nothing to resume in '{project}'")
            if run_id is not None and run_id != found.id:
                raise NotFoundError(f"run {run_id} is not the run to resume in '{project}'")
            return self._continue(settings, workspace, run_log, found, None)

    def _continue(
        self,
        settings: Project,
        workspace: Path,
        run_log: RunLog,
        found: Run,
        integrator: Integrator | None,
    ) -> Run:
        """Pick ``found`` up again in its kept worktree, from where its attempts left off."""
        project = settings.name
        with self._mutex:
            lock = take_run_lock(workspace, project)
            try:
                with user_errors():
                    ticket = load_ticket(project, found.ticket_id, projects_dir=self.projects_dir)
                    manager = self._manager(settings)
                    worktree = manager.resume(ticket.id)
                    if found.status is RunStatus.INTERRUPTED:
                        run = run_log.reopen_run(found.id)
                    else:
                        run = run_log.set_run_status(found.id, RunStatus.RUNNING)
                    if found.status is RunStatus.AWAITING_APPROVAL:
                        self._ticket_status(project, ticket.id, "running")
                    if worktree is None:
                        reason = (
                            f"the worktree of {ticket.id} is gone; "
                            f"discard it with `spool run discard {ticket.id}`"
                        )
                        self._active.pop(project, None)
                        run_log.set_run_status(found.id, RunStatus.BLOCKED, reason)
                        self._ticket_status(project, ticket.id, "blocked")
                        raise RunLoopError(reason)
                    ctx = self._context(
                        settings, workspace, run_log, ticket, run, manager, worktree, integrator
                    )
            except BaseException:
                lock.release()
                raise
            self.timer.cancel(project)
            active = Active(ticket.id, found.id, Flags(), lock=lock)
            self._active[project] = active
            ctx.phase("resumed", f"{ticket.id} · resumed (run {found.id})")
            self._spawn(active, ctx, next_kind(run_log.list_attempts(found.id)), False)
            return ctx.run

    def integrate_ticket(self, project: str, ticket_id: str) -> Run:
        """Integrate an approved ticket waiting in ``awaiting_approval`` (a dirty main
        checkout, an interrupted integration, or ``run.integration: hold``)."""
        settings, workspace, run_log = self._project(project)
        with self._mutex:
            self._check_free(project)
            with user_errors():
                ticket = load_ticket(project, ticket_id, projects_dir=self.projects_dir)
                runs = run_log.list_runs(ticket_id=ticket_id, limit=1)
            latest, status = runs[0] if runs else None, ticket.meta.status
            if status != "awaiting_approval" or latest is None or latest.status != status:
                raise RunLoopError(f"{ticket_id} is {status}, not awaiting approval")
            # Always the real integrator: this is how a held ticket gets merged.
            return self._continue(settings, workspace, run_log, latest, self.integrator)

    def discard(self, project: str, ticket_id: str) -> None:
        """Remove the worktree of an interrupted or blocked ticket; ticket back to ``ready``."""
        settings, _, run_log = self._project(project)
        with self._mutex:
            active = self._active.get(project)
            if active is not None and active.ticket_id == ticket_id:
                raise RunActiveError(
                    f"{ticket_id} has an active run (run {active.run_id}); "
                    "cancel it with `spool run cancel`"
                )
            with user_errors():
                ticket = load_ticket(project, ticket_id, projects_dir=self.projects_dir)
                runs = run_log.list_runs(ticket_id=ticket_id, limit=1)
                status = ticket.meta.status
                interrupted = bool(runs) and runs[0].status is RunStatus.INTERRUPTED
                if not (status == "blocked" or (status == "running" and interrupted)):
                    raise RunLoopError(
                        f"{ticket_id} is {status}; only a blocked ticket or one whose run "
                        "was interrupted can be discarded"
                    )
                self._manager(settings).teardown(ticket_id)
                self._ticket_status(project, ticket_id, "ready")
            if runs:
                record_phase(run_log, runs[0].id, "discarded", f"{ticket_id} · discarded")

    def current(self, project: str) -> Current:
        _, _, run_log = self._project(project)
        with self._mutex:
            active = self._active.get(project)
            working = active is not None and active.thread is not None
            run_id = active.run_id if active is not None else None
        runs = [run_log.get_run(run_id)] if run_id is not None else run_log.list_runs(limit=1)
        run = runs[0] if runs else None
        if run is None:
            return Current(project, False, False, None, 0, None, ())
        events = run_log.events_since(0, run_id=run.id, limit=100_000)
        return Current(
            project=project,
            active=active is not None,
            working=working,
            run=run,
            attempts=len(run_log.list_attempts(run.id)),
            usage=run_log.run_usage(run.id),
            phases=tuple(
                (event.id, str(event.payload.get("text", "")))
                for event in events
                if event.kind is EventKind.RUN_PHASE
            ),
            last_merged=last_merged(run_log),
        )

    def wait(self, project: str, timeout: float | None = None) -> None:
        """Wait for the project's worker thread to finish (tests, shutdown)."""
        with self._mutex:
            active = self._active.get(project)
            thread = active.thread if active is not None else None
        if thread is not None:
            thread.join(timeout)

    def close(self) -> None:
        """Daemon shutdown: stop the timer and the agents; runs are left for recovery."""
        self.timer.close()
        with self._mutex:
            threads = []
            for active in self._active.values():
                if active.thread is not None:
                    active.flags.stop.set()
                    active.flags.cancel.set()
                    threads.append(active.thread)
        for thread in threads:
            thread.join(SHUTDOWN_WAIT_S)
