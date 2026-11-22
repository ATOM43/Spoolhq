"""One-way sync of tickets to a project's tracker, through the outbox (docs/tracker.md).

Nothing else calls the tracker. Every ``POLL_S`` a background thread, for each project
with a ``tracker`` block: queues what changed since the last look (a ticket's content
or status, a finished run's comment, a run's pull request; see ``services/runs/outbox``),
then sends the due actions one at a time. A failure retries after 5 s, doubling up to
10 min; after 5 the action fails, the project's sync state becomes ``failed`` and a
``tracker.failed`` event is recorded on the ticket's latest run. A rate limit waits
as long as the tracker says. A success clears the failed state. The run loop never
waits on any of it.
"""

import hashlib
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, cast

import httpx

from spoolhq.services.projects import ProjectError, edit_lock, load_project, project_dir
from spoolhq.services.projects.model import Tracker
from spoolhq.services.runs import EventKind, Run, RunKind, RunLog, RunRegistry, outbox
from spoolhq.services.runs.db import utc_now
from spoolhq.services.scheduler import tickets_lock
from spoolhq.services.secrets import SECRETS, SecretName, read_secret
from spoolhq.services.tickets import (
    Ticket,
    TicketError,
    TicketValidationError,
    list_tickets,
    load_ticket,
    save_ticket,
)
from spoolhq.services.tracker.base import TrackerAdapter, TrackerError
from spoolhq.services.tracker.registry import make_adapter

logger = logging.getLogger(__name__)

SyncStateName = Literal["off", "ok", "syncing", "failed"]
POLL_S = 5.0
FIRST_RETRY_S = 5
MAX_RETRY_S = 600
RUNS_SCANNED = 200
"""How many of the newest runs are checked for a comment or PR link to queue."""

AdapterFactory = Callable[[Tracker, str, httpx.BaseTransport | None], TrackerAdapter]


@dataclass(frozen=True)
class TrackerStatus:
    kind: str | None
    state: SyncStateName
    pending: int
    last_error: str | None
    last_synced_at: str | None
    failed_at: str | None


def fingerprint(ticket: Ticket) -> str:
    """What a push sends besides the status; ``tracker_ref`` isn't part of it."""
    return hashlib.sha256(f"{ticket.meta.title}\n{ticket.body}".encode()).hexdigest()


def retry_delay(failures: int) -> timedelta:
    return timedelta(seconds=min(FIRST_RETRY_S * 2 ** (failures - 1), MAX_RETRY_S))


def no_token(kind: str) -> str:
    return f"No {kind} token; set it in Settings or {SECRETS[cast(SecretName, kind)][0]}"


def run_comment(run_log: RunLog, run: Run) -> str:
    """Built from run data only, never from ticket text."""
    usage = run_log.run_usage(run.id)
    spent = f"{usage.total_tokens:,} tokens"
    if usage.cost_micro_usd is not None:
        spent += f" · ${usage.cost_micro_usd / 1_000_000:.2f}"
    lines = [
        f"SpoolHQ run {run.id}: {run.status.value}",
        f"Attempts: {len(run_log.list_attempts(run.id))}",
        f"Usage: {spent}",
    ]
    commit = outbox.run_commit(run_log, run.id)
    if run.pr_url:
        lines.append(f"Pull request: {run.pr_url}")
    elif commit:
        lines.append(f"Commit: {commit}")
    return "\n".join(lines)


class TrackerSync:
    def __init__(
        self,
        registry: RunRegistry,
        *,
        projects_dir: Path,
        transport: httpx.BaseTransport | None = None,
        clock: Callable[[], datetime] = utc_now,
        interval_s: float = POLL_S,
        adapters: AdapterFactory = make_adapter,
    ) -> None:
        self.registry = registry
        self.projects_dir = projects_dir
        self.transport = transport
        self.clock = clock
        self.interval_s = interval_s
        self.make_adapter = adapters
        self.wait_until: dict[str, datetime] = {}
        """Set by a rate limit: no call for that project before then."""
        self._adapters: dict[str, tuple[str, TrackerAdapter]] = {}
        self._lock = threading.Lock()
        """Held while sending, so one action at a time goes out."""
        self._start_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # The thread -----------------------------------------------------------------------

    def start_if_needed(self) -> None:
        """Start the thread once any project has a ``tracker`` block."""
        with self._start_lock:
            if self._thread is not None or self._stop.is_set():
                return
            if not any(self.settings(project) for project in self.registry.projects):
                return
            self._thread = threading.Thread(target=self._poll, name="spoolhq-tracker", daemon=True)
            self._thread.start()

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(self.interval_s)
        with self._lock:
            for _, adapter in self._adapters.values():
                adapter.close()
            self._adapters.clear()

    def _poll(self) -> None:
        while not self._stop.wait(self.interval_s):
            for project in self.registry.projects:
                try:
                    self.tick(project)
                except Exception:
                    logger.exception("tracker sync failed", extra={"project": project})

    # Per project ----------------------------------------------------------------------

    def settings(self, project: str) -> Tracker | None:
        try:
            return load_project(project, projects_dir=self.projects_dir).tracker
        except ProjectError:
            return None

    def _run_log(self, project: str) -> RunLog:
        return self.registry.open(project_dir(project, projects_dir=self.projects_dir)).run_log

    def tick(self, project: str) -> int:
        """Queue what changed, then send what is due; returns how many were sent."""
        tracker = self.settings(project)
        if tracker is None:
            return 0
        self.scan(project, tracker)
        return self.drain(project, tracker)

    def scan(self, project: str, tracker: Tracker, *, force: bool = False) -> int:
        """Queue every change since the last scan (with ``force``, a push of every
        ticket); returns how many actions were queued."""
        run_log = self._run_log(project)
        now = self.clock()
        queued = 0
        for ticket in list_tickets(project, projects_dir=self.projects_dir).tickets:
            action = outbox.queue_ticket(
                run_log, ticket.id, fingerprint(ticket), ticket.meta.status, now, force=force
            )
            queued += action is not None
        baseline = outbox.baseline_run_id(run_log)
        sent = outbox.queued_keys(run_log)
        for run in run_log.list_runs(limit=RUNS_SCANNED):
            if run.kind is not RunKind.TICKET or run.id <= baseline:
                continue
            key = f"comment:{run.id}"
            if tracker.comment_on_runs and run.status.is_terminal and key not in sent:
                text = run_comment(run_log, run)
                queued += outbox.queue_once(run_log, run.ticket_id, "comment", run.id, text, now)
            if run.pr_url and f"link_pr:{run.id}" not in sent:
                queued += outbox.queue_once(
                    run_log, run.ticket_id, "link_pr", run.id, run.pr_url, now
                )
        return queued

    def push_all(self, project: str) -> int:
        """Queue a push of every ticket (``spool tracker push``); ProjectError without a
        ``tracker`` block."""
        tracker = load_project(project, projects_dir=self.projects_dir).tracker
        if tracker is None:
            raise ProjectError(f"'{project}' has no tracker block in project.yaml")
        queued = self.scan(project, tracker, force=True)
        self.start_if_needed()
        return queued

    def retry(self, project: str) -> int:
        """Re-queue the failed actions and clear the failed state; returns how many were
        re-queued (0: nothing failed, nothing changed). ProjectError without a ``tracker``
        block."""
        tracker = load_project(project, projects_dir=self.projects_dir).tracker
        if tracker is None:
            raise ProjectError(f"'{project}' has no tracker block in project.yaml")
        queued = outbox.retry_failed(self._run_log(project), self.clock())
        self.start_if_needed()
        return queued

    def status(self, project: str) -> TrackerStatus:
        tracker = load_project(project, projects_dir=self.projects_dir).tracker
        if tracker is None:
            return TrackerStatus(None, "off", 0, None, None, None)
        self.start_if_needed()  # a tracker block added by hand starts sync on the next look
        found = outbox.sync_state(self._run_log(project))
        state: SyncStateName = (
            "failed" if found.last_error else "syncing" if found.pending else "ok"
        )
        return TrackerStatus(
            tracker.kind,
            state,
            found.pending,
            found.last_error,
            found.last_synced_at,
            found.failed_at,
        )

    def drain(self, project: str, tracker: Tracker) -> int:
        """Send the due actions one at a time, oldest first, until none is due."""
        run_log = self._run_log(project)
        sent = 0
        with self._lock:
            while not self._stop.is_set():
                now = self.clock()
                if project in self.wait_until and now < self.wait_until[project]:
                    break
                action = outbox.due_action(run_log, now)
                if action is None:
                    break
                try:
                    self._send(project, tracker, action)
                except TrackerError as exc:
                    if exc.retry_after is not None:
                        until = now + timedelta(seconds=exc.retry_after)
                        self.wait_until[project] = until
                        outbox.defer(run_log, action.id, until)
                        break
                    self._failed(project, run_log, action, str(exc), now)
                    continue
                outbox.mark_sent(run_log, action.id, self.clock())
                sent += 1
        return sent

    def _failed(
        self, project: str, run_log: RunLog, action: outbox.OutboxAction, error: str, now: datetime
    ) -> None:
        failures = action.failures + 1
        final = outbox.mark_failure(run_log, action.id, error, now, retry_delay(failures))
        details = {"action": action.action, "ticket_id": action.ticket_id, "error": error}
        logger.warning(
            "tracker action failed", extra={"project": project, "failures": failures, **details}
        )
        if not final:
            return
        runs = run_log.list_runs(action.ticket_id, limit=1)
        run_id = action.run_id or (runs[0].id if runs else None)
        if run_id is not None:
            run_log.append_event(run_id, EventKind.TRACKER_FAILED, details)

    def _adapter(self, project: str, tracker: Tracker) -> TrackerAdapter:
        token = read_secret(cast(SecretName, tracker.kind))
        if token is None:
            raise TrackerError(no_token(tracker.kind))
        # A new adapter when the settings or the token change; the key never leaves here.
        key = hashlib.sha256(f"{tracker.model_dump_json()}\n{token}".encode()).hexdigest()
        cached = self._adapters.get(project)
        if cached is not None and cached[0] == key:
            return cached[1]
        if cached is not None:
            cached[1].close()
        adapter = self.make_adapter(tracker, token, self.transport)
        self._adapters[project] = (key, adapter)
        return adapter

    def _send(self, project: str, tracker: Tracker, action: outbox.OutboxAction) -> None:
        try:
            ticket = load_ticket(project, action.ticket_id, projects_dir=self.projects_dir)
        except TicketValidationError:
            raise TrackerError(f"{action.ticket_id}'s ticket file is invalid") from None
        except TicketError:
            return  # deleted locally: its task is left alone (one-way sync)
        adapter = self._adapter(project, tracker)
        ref = ticket.meta.tracker_ref
        if action.action == "push" or ref is None:
            ref = adapter.push_ticket(ticket)
            if ticket.meta.tracker_ref != ref:
                self._write_ref(project, ticket.id, ref)
            if action.action in ("push", "status"):
                return
        if action.action == "status":
            adapter.update_status(ref, ticket.meta.status)
        elif action.action == "comment":
            adapter.comment(ref, action.text or "")
        else:
            adapter.link_pr(ref, action.text or "")

    def _write_ref(self, project: str, ticket_id: str, ref: str) -> None:
        """Store the task's ref in the ticket, under the ticket locks, through the store."""
        workspace = project_dir(project, projects_dir=self.projects_dir)
        with edit_lock(workspace), tickets_lock(workspace):
            ticket = load_ticket(project, ticket_id, projects_dir=self.projects_dir)
            ticket.meta.tracker_ref = ref
            save_ticket(project, ticket, projects_dir=self.projects_dir)
