"""The run log: every run, attempt and event of a workspace, in ``state.db``.

Each method is one transaction, and a lifecycle change appends its event in the same
transaction. Events reach the bus only after their transaction commits, in id order;
a failed transaction publishes nothing.
"""

import os
import shutil
import sqlite3
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Self

from spoolhq.core.ids import check_ticket_id
from spoolhq.services.runs import db
from spoolhq.services.runs.bus import EventBus
from spoolhq.services.runs.db import Clock
from spoolhq.services.runs.model import (
    Attempt,
    AttemptKind,
    AttemptStatus,
    Event,
    EventKind,
    Run,
    RunStatus,
    Usage,
)
from spoolhq.services.runs.rows import (
    ATTEMPT_COLUMNS,
    EVENT_COLUMNS,
    RUN_COLUMNS,
    Transaction,
    encode_payload,
    event_kind,
    fetch_run,
    to_event,
    to_run,
)

RUNS_DIR = "runs"
READ_ONLY_INSTANCE = "read-only"


def _check_count(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer, got {value!r}")
    if value < 0:
        raise ValueError(f"{name} must not be negative, got {value}")


def attempt_dir_name(ticket_id: str, number: int) -> str:
    """``runs/<ticket>/<NNN>``, always with forward slashes."""
    return f"{RUNS_DIR}/{check_ticket_id(ticket_id)}/{number:03d}"


class RunLog:
    """The run history of one workspace, over one SQLite connection.

    Thread-safe: every operation holds a lock around its transaction. Use it as a
    context manager, or call ``close``.
    """

    def __init__(
        self,
        workspace: Path,
        *,
        bus: EventBus | None = None,
        clock: Clock = db.utc_now,
        daemon_instance: str,
        _read_only: bool = False,
    ) -> None:
        if not daemon_instance:
            raise ValueError("daemon_instance must not be empty")
        self.workspace = workspace
        self.bus = bus
        self.daemon_instance = daemon_instance
        self.read_only = _read_only
        self._clock = clock
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = db.connect(workspace, read_only=_read_only)

    @classmethod
    def open_read_only(cls, workspace: Path) -> "RunLog":
        """Open an existing ``state.db`` for reading only: no migration, no writes.

        Raises FileNotFoundError when the workspace has no ``state.db`` yet.
        """
        return cls(workspace, daemon_instance=READ_ONLY_INSTANCE, _read_only=True)

    @property
    def db_path(self) -> Path:
        return db.state_db_path(self.workspace)

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    # Transactions ---------------------------------------------------------------------

    def _connection(self) -> sqlite3.Connection:
        if self._conn is None:
            raise ValueError("the run log is closed")
        return self._conn

    @contextmanager
    def transaction(self) -> Iterator[Transaction]:
        """One ``BEGIN IMMEDIATE`` … ``COMMIT``; its events are published after commit.

        For the runs package (recovery); other callers use the methods below.
        """
        if self.read_only:
            raise ValueError("the run log is open read-only")
        with self._lock:
            conn = self._connection()
            tx = Transaction(conn=conn, clock=self._clock)
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield tx
                conn.execute("COMMIT")
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                tx.rolled_back()
                raise
            # Still under the lock, so events from concurrent operations reach the bus
            # in id order. publish never blocks.
            if self.bus is not None:
                for event in tx.events:
                    self.bus.publish(event)

    @contextmanager
    def _reading(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            conn = self._connection()
            conn.execute("BEGIN")
            try:
                yield conn
            finally:
                if conn.in_transaction:
                    conn.execute("COMMIT")

    # Rows -----------------------------------------------------------------------------

    def _run(self, conn: sqlite3.Connection, run_id: int) -> Run:
        return fetch_run(conn, run_id)

    def _attempt(self, conn: sqlite3.Connection, attempt_id: int) -> Attempt:
        row = conn.execute(
            f"SELECT {ATTEMPT_COLUMNS} FROM attempts WHERE id = ?",  # noqa: S608 - constant columns
            (attempt_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"attempt {attempt_id} not found")
        return self._to_attempt(row)

    def _to_attempt(self, row: tuple[Any, ...]) -> Attempt:
        return Attempt(
            id=row[0],
            run_id=row[1],
            ticket_id=row[2],
            number=row[3],
            kind=AttemptKind(row[4]),
            status=AttemptStatus(row[5]),
            dir=row[6],
            backend=row[7],
            model=row[8],
            input_tokens=row[9],
            output_tokens=row[10],
            cost_micro_usd=row[11],
            started_at=row[12],
            ended_at=row[13],
            workspace=self.workspace,
            cache_read_tokens=row[14],
        )

    @staticmethod
    def _check_open(run: Run) -> None:
        if run.status.is_terminal:
            raise ValueError(f"run {run.id} is already {run.status.value}")

    # Writes ---------------------------------------------------------------------------

    def start_run(self, ticket_id: str) -> Run:
        """Start a run for ``ticket_id`` in status ``running``; event ``run.started``."""
        check_ticket_id(ticket_id)
        with self.transaction() as tx:
            cursor = tx.conn.execute(
                "INSERT INTO runs (ticket_id, status, daemon_instance, started_at) "
                "VALUES (?, ?, ?, ?)",
                (ticket_id, RunStatus.RUNNING.value, self.daemon_instance, tx.now()),
            )
            assert cursor.lastrowid is not None  # noqa: S101 - an INSERT always sets it
            run = self._run(tx.conn, cursor.lastrowid)
            tx.append_event(run.id, EventKind.RUN_STARTED, {"ticket_id": ticket_id})
            return run

    def set_run_status(
        self,
        run_id: int,
        status: RunStatus | str,
        reason: str | None = None,
        *,
        reset_at: datetime | None = None,
    ) -> Run:
        """Move a run to ``status``; a terminal status sets ``ended_at``.

        ``reset_at`` is stored for a run paused by a usage limit and cleared by any other
        change. Raises ValueError if the run has already ended. Event ``run.status``.
        """
        new = RunStatus(status)
        reset = db.format_ts(reset_at) if reset_at is not None else None
        with self.transaction() as tx:
            run = self._run(tx.conn, run_id)
            self._check_open(run)
            ended_at = tx.now() if new.is_terminal else None
            tx.conn.execute(
                "UPDATE runs SET status = ?, reason = ?, ended_at = ?, reset_at = ? WHERE id = ?",
                (new.value, reason, ended_at, reset, run_id),
            )
            payload = {"from": run.status.value, "to": new.value, "reason": reason}
            if reset is not None:
                payload["reset_at"] = reset
            tx.append_event(run_id, EventKind.RUN_STATUS, payload)
            return self._run(tx.conn, run_id)

    def reopen_run(self, run_id: int) -> Run:
        """Move an ``interrupted`` run back to ``running`` under this daemon instance.

        The one way out of a terminal status: the run loop resumes a run a stopped
        daemon left behind, in its kept worktree. Event ``run.status``.
        """
        with self.transaction() as tx:
            run = self._run(tx.conn, run_id)
            if run.status is not RunStatus.INTERRUPTED:
                raise ValueError(f"run {run_id} is {run.status.value}, not interrupted")
            tx.conn.execute(
                "UPDATE runs SET status = ?, reason = NULL, ended_at = NULL, reset_at = NULL, "
                "daemon_instance = ? WHERE id = ?",
                (RunStatus.RUNNING.value, self.daemon_instance, run_id),
            )
            tx.append_event(
                run_id,
                EventKind.RUN_STATUS,
                {"from": run.status.value, "to": RunStatus.RUNNING.value, "reason": "resumed"},
            )
            return self._run(tx.conn, run_id)

    def set_progress_note(self, run_id: int, note: str | None) -> Run:
        """Store the implementer's progress note on the run (T14 appends it to PROGRESS.md)."""
        with self.transaction() as tx:
            self._run(tx.conn, run_id)
            tx.conn.execute("UPDATE runs SET progress_note = ? WHERE id = ?", (note, run_id))
            return self._run(tx.conn, run_id)

    def start_attempt(
        self,
        run_id: int,
        kind: AttemptKind | str,
        backend: str | None = None,
        model: str | None = None,
    ) -> Attempt:
        """Start the ticket's next attempt and create its folder ``runs/<ticket>/<NNN>/``.

        Numbers count per ticket across all its runs. Event ``attempt.started``.
        """
        attempt_kind = AttemptKind(kind)
        with self.transaction() as tx:
            run = self._run(tx.conn, run_id)
            self._check_open(run)
            ticket_id = check_ticket_id(run.ticket_id)
            number: int = tx.conn.execute(
                "SELECT COALESCE(MAX(number), 0) + 1 FROM attempts WHERE ticket_id = ?",
                (ticket_id,),
            ).fetchone()[0]
            rel_dir = attempt_dir_name(ticket_id, number)
            cursor = tx.conn.execute(
                "INSERT INTO attempts (run_id, ticket_id, number, kind, status, dir, backend, "
                "model, started_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    ticket_id,
                    number,
                    attempt_kind.value,
                    AttemptStatus.RUNNING.value,
                    rel_dir,
                    backend,
                    model,
                    tx.now(),
                ),
            )
            assert cursor.lastrowid is not None  # noqa: S101 - an INSERT always sets it
            attempt = self._attempt(tx.conn, cursor.lastrowid)
            tx.append_event(
                run_id,
                EventKind.ATTEMPT_STARTED,
                {
                    "number": number,
                    "kind": attempt_kind.value,
                    "dir": rel_dir,
                    "backend": backend,
                    "model": model,
                },
                attempt_id=attempt.id,
            )
            folder = self.workspace / rel_dir
            _make_attempt_dir(folder)
            tx.on_rollback(lambda: shutil.rmtree(folder, ignore_errors=True))
            return attempt

    def finish_attempt(self, attempt_id: int, status: AttemptStatus | str) -> Attempt:
        """End a running attempt with ``status``; sets ``ended_at``. Event
        ``attempt.finished``."""
        new = AttemptStatus(status)
        if new is AttemptStatus.RUNNING:
            raise ValueError("an attempt cannot finish as running")
        with self.transaction() as tx:
            attempt = self._attempt(tx.conn, attempt_id)
            if attempt.status is not AttemptStatus.RUNNING:
                raise ValueError(f"attempt {attempt_id} is already {attempt.status.value}")
            tx.conn.execute(
                "UPDATE attempts SET status = ?, ended_at = ? WHERE id = ?",
                (new.value, tx.now(), attempt_id),
            )
            tx.append_event(
                attempt.run_id,
                EventKind.ATTEMPT_FINISHED,
                {"number": attempt.number, "status": new.value},
                attempt_id=attempt_id,
            )
            return self._attempt(tx.conn, attempt_id)

    def record_usage(
        self,
        attempt_id: int,
        input_tokens: int,
        output_tokens: int,
        cost_micro_usd: int | None = None,
        cache_read_tokens: int = 0,
    ) -> Attempt:
        """Add tokens and cost (micro-USD) to an attempt's totals.

        ``cache_read_tokens`` is the part of ``input_tokens`` read from the cache. A
        None cost leaves the stored cost as it is; a stored NULL plus a value becomes
        that value. Negative numbers, or more cache reads than input, raise ValueError.
        """
        _check_count("input_tokens", input_tokens)
        _check_count("output_tokens", output_tokens)
        _check_count("cache_read_tokens", cache_read_tokens)
        if cache_read_tokens > input_tokens:
            raise ValueError("cache_read_tokens is part of input_tokens and can't exceed it")
        if cost_micro_usd is not None:
            _check_count("cost_micro_usd", cost_micro_usd)
        with self.transaction() as tx:
            self._attempt(tx.conn, attempt_id)
            tx.conn.execute(
                "UPDATE attempts SET input_tokens = input_tokens + ?, "
                "output_tokens = output_tokens + ?, "
                "cache_read_tokens = cache_read_tokens + ?, "
                "cost_micro_usd = CASE WHEN ? IS NULL THEN cost_micro_usd "
                "ELSE COALESCE(cost_micro_usd, 0) + ? END "
                "WHERE id = ?",
                (
                    input_tokens,
                    output_tokens,
                    cache_read_tokens,
                    cost_micro_usd,
                    cost_micro_usd,
                    attempt_id,
                ),
            )
            return self._attempt(tx.conn, attempt_id)

    def append_event(
        self,
        run_id: int,
        kind: EventKind | str,
        payload: Mapping[str, Any],
        attempt_id: int | None = None,
    ) -> Event:
        """Append an event. ``payload`` must be a JSON-serialisable dict of at most
        64 KiB once encoded; large content belongs in the attempt's files."""
        event_kind(kind)
        encode_payload(payload)
        with self.transaction() as tx:
            if attempt_id is not None:
                attempt = self._attempt(tx.conn, attempt_id)
                if attempt.run_id != run_id:
                    raise ValueError(f"attempt {attempt_id} belongs to run {attempt.run_id}")
            return tx.append_event(run_id, kind, payload, attempt_id=attempt_id)

    # Reads ----------------------------------------------------------------------------

    def get_run(self, run_id: int) -> Run:
        with self._reading() as conn:
            return self._run(conn, run_id)

    def get_attempt(self, attempt_id: int) -> Attempt:
        with self._reading() as conn:
            return self._attempt(conn, attempt_id)

    def list_runs(self, ticket_id: str | None = None, limit: int = 50) -> list[Run]:
        """Runs, newest first, optionally of one ticket."""
        if ticket_id is not None:
            check_ticket_id(ticket_id)
        with self._reading() as conn:
            rows = conn.execute(
                f"SELECT {RUN_COLUMNS} FROM runs WHERE ? IS NULL OR ticket_id = ? "  # noqa: S608 - constant columns
                "ORDER BY id DESC LIMIT ?",
                (ticket_id, ticket_id, limit),
            ).fetchall()
        return [to_run(row) for row in rows]

    def list_attempts(self, run_id: int) -> list[Attempt]:
        """A run's attempts in order. Raises KeyError for an unknown run."""
        with self._reading() as conn:
            self._run(conn, run_id)
            rows = conn.execute(
                f"SELECT {ATTEMPT_COLUMNS} FROM attempts WHERE run_id = ? ORDER BY number",  # noqa: S608 - constant columns
                (run_id,),
            ).fetchall()
        return [self._to_attempt(row) for row in rows]

    def run_usage(self, run_id: int) -> Usage:
        """Tokens and cost summed over a run's attempts."""
        with self._reading() as conn:
            self._run(conn, run_id)
            row = conn.execute(
                "SELECT COALESCE(SUM(input_tokens), 0), COALESCE(SUM(output_tokens), 0), "
                "SUM(cost_micro_usd), COALESCE(SUM(cache_read_tokens), 0) "
                "FROM attempts WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        return Usage(
            input_tokens=row[0],
            output_tokens=row[1],
            cost_micro_usd=row[2],
            cache_read_tokens=row[3],
        )

    def last_event_id(self) -> int:
        """The highest event id in the database, or 0 if there are no events."""
        with self._reading() as conn:
            row = conn.execute("SELECT COALESCE(MAX(id), 0) FROM events").fetchone()
        return int(row[0])

    def events_since(
        self, after_id: int, run_id: int | None = None, limit: int = 1000
    ) -> list[Event]:
        """Events with an id above ``after_id`` in id order, optionally of one run."""
        with self._reading() as conn:
            rows = conn.execute(
                f"SELECT {EVENT_COLUMNS} FROM events WHERE id > ? "  # noqa: S608 - constant columns
                "AND (? IS NULL OR run_id = ?) ORDER BY id LIMIT ?",
                (after_id, run_id, run_id, limit),
            ).fetchall()
        return [to_event(row) for row in rows]


def _make_attempt_dir(folder: Path) -> None:
    """Create a new attempt folder; an empty one left by a transaction that never
    committed (the daemon died between mkdir and commit) is reused."""
    try:
        folder.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        if not folder.is_dir() or any(folder.iterdir()):
            raise
        os.rmdir(folder)
        folder.mkdir(exist_ok=False)
