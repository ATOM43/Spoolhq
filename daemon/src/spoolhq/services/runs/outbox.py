"""The tracker outbox (T24): actions waiting to be sent to a project's tracker, stored in
``state.db`` so nothing the run loop does ever waits on the tracker (docs/tracker.md).

``push`` and ``status`` rows are coalesced: at most one of each pending per ticket, and a
pending push covers a status change. ``comment`` and ``link_pr`` rows carry a
``once_key`` (``comment:<run id>``) that is never deleted, so each is queued only once,
across restarts too.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from spoolhq.services.runs.db import format_ts
from spoolhq.services.runs.log import RunLog

Action = Literal["push", "status", "comment", "link_pr"]
MAX_FAILURES = 5


@dataclass(frozen=True)
class OutboxAction:
    id: int
    ticket_id: str
    action: Action
    run_id: int | None
    text: str | None
    failures: int


@dataclass(frozen=True)
class SyncState:
    pending: int
    last_error: str | None
    last_synced_at: str | None
    failed_at: str | None


def baseline_run_id(run_log: RunLog) -> int:
    """Runs up to this id ended before sync started and get no comment; set on first use."""
    with run_log.transaction() as tx:
        row = tx.conn.execute("SELECT baseline_run_id FROM tracker_sync WHERE id = 1").fetchone()
        if row is not None:
            return int(row[0])
        latest = int(tx.conn.execute("SELECT COALESCE(MAX(id), 0) FROM runs").fetchone()[0])
        tx.conn.execute("INSERT INTO tracker_sync (id, baseline_run_id) VALUES (1, ?)", (latest,))
        return latest


def peek_baseline(run_log: RunLog) -> int:
    """``baseline_run_id`` without setting it: before sync starts, the latest run."""
    with run_log._reading() as conn:
        row = conn.execute("SELECT baseline_run_id FROM tracker_sync WHERE id = 1").fetchone()
        latest = conn.execute("SELECT COALESCE(MAX(id), 0) FROM runs").fetchone()[0]
    return int(row[0]) if row else int(latest)


def _pending(conn: sqlite3.Connection, ticket_id: str, action: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM tracker_outbox WHERE ticket_id = ? AND action = ? AND state = 'pending'",
        (ticket_id, action),
    ).fetchone()
    return row is not None


def queue_ticket(
    run_log: RunLog,
    ticket_id: str,
    fingerprint: str,
    status: str,
    now: datetime,
    *,
    force: bool = False,
) -> Action | None:
    """Queue a push when the ticket is new, its content changed or ``force``; a status
    update when only its status changed. Returns what was queued (None: nothing new)."""
    with run_log.transaction() as tx:
        conn = tx.conn
        row = conn.execute(
            "SELECT fingerprint, status FROM tracker_tickets WHERE ticket_id = ?", (ticket_id,)
        ).fetchone()
        action: Action | None = None
        if force or row is None or row[0] != fingerprint:
            action = "push"
        elif row[1] != status:
            action = "status"
        conn.execute(
            "INSERT INTO tracker_tickets (ticket_id, fingerprint, status) VALUES (?, ?, ?) "
            "ON CONFLICT (ticket_id) DO UPDATE SET fingerprint = excluded.fingerprint, "
            "status = excluded.status",
            (ticket_id, fingerprint, status),
        )
        if action is None or _pending(conn, ticket_id, "push"):
            return None  # a pending push sends the latest content and status
        if action == "push":
            conn.execute(
                "DELETE FROM tracker_outbox "
                "WHERE ticket_id = ? AND action = 'status' AND state = 'pending'",
                (ticket_id,),
            )
        elif _pending(conn, ticket_id, "status"):
            return None  # it sends the ticket's status when it goes out
        _insert(conn, ticket_id, action, None, None, None, now)
        return action


def queue_once(
    run_log: RunLog, ticket_id: str, action: Action, run_id: int, text: str, now: datetime
) -> bool:
    """Queue a run's comment or PR link unless it was ever queued; True if queued now."""
    with run_log.transaction() as tx:
        return _insert(tx.conn, ticket_id, action, run_id, text, f"{action}:{run_id}", now)


def _insert(
    conn: sqlite3.Connection,
    ticket_id: str,
    action: Action,
    run_id: int | None,
    text: str | None,
    once_key: str | None,
    now: datetime,
) -> bool:
    cursor = conn.execute(
        "INSERT OR IGNORE INTO tracker_outbox (ticket_id, action, run_id, text, once_key, "
        "state, next_at, created_at) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)",
        (ticket_id, action, run_id, text, once_key, format_ts(now), format_ts(now)),
    )
    return bool(cursor.rowcount)


def due_action(run_log: RunLog, now: datetime) -> OutboxAction | None:
    """The oldest pending action whose retry time has come."""
    with run_log._reading() as conn:
        row = conn.execute(
            "SELECT id, ticket_id, action, run_id, text, failures FROM tracker_outbox "
            "WHERE state = 'pending' AND next_at <= ? ORDER BY id LIMIT 1",
            (format_ts(now),),
        ).fetchone()
    return OutboxAction(*row) if row else None


def mark_sent(run_log: RunLog, action_id: int, now: datetime) -> None:
    """Done; a success also clears the project's failed state."""
    with run_log.transaction() as tx:
        tx.conn.execute("UPDATE tracker_outbox SET state = 'done' WHERE id = ?", (action_id,))
        tx.conn.execute(
            "UPDATE tracker_sync SET last_error = NULL, failed_at = NULL, last_synced_at = ? "
            "WHERE id = 1",
            (format_ts(now),),
        )


def mark_failure(
    run_log: RunLog, action_id: int, error: str, now: datetime, retry_in: timedelta
) -> bool:
    """Count a failure: retry after ``retry_in``, or after ``MAX_FAILURES`` mark the action
    and the project's sync as failed. True when it failed for good."""
    with run_log.transaction() as tx:
        conn = tx.conn
        row = conn.execute(
            "UPDATE tracker_outbox SET failures = failures + 1, last_error = ?, next_at = ? "
            "WHERE id = ? RETURNING failures",
            (error, format_ts(now + retry_in), action_id),
        ).fetchone()
        if row is None or row[0] < MAX_FAILURES:
            return False
        conn.execute("UPDATE tracker_outbox SET state = 'failed' WHERE id = ?", (action_id,))
        conn.execute(
            "UPDATE tracker_sync SET last_error = ?, failed_at = ? WHERE id = 1",
            (error, format_ts(now)),
        )
        return True


def retry_failed(run_log: RunLog, now: datetime) -> int:
    """Put every failed action back in the queue with no failures counted, and clear the
    project's failed state; returns how many were re-queued. As when queuing, a ticket
    keeps at most one pending push and one status update, and a pending push covers a
    status update."""
    with run_log.transaction() as tx:
        conn = tx.conn
        conn.execute(
            "DELETE FROM tracker_outbox WHERE state = 'failed' AND action IN ('push', 'status') "
            "AND EXISTS (SELECT 1 FROM tracker_outbox AS p WHERE p.state = 'pending' "
            "AND p.ticket_id = tracker_outbox.ticket_id "
            "AND (p.action = 'push' OR p.action = tracker_outbox.action))"
        )
        cursor = conn.execute(
            "UPDATE tracker_outbox SET state = 'pending', failures = 0, last_error = NULL, "
            "next_at = ? WHERE state = 'failed'",
            (format_ts(now),),
        )
        conn.execute(
            "DELETE FROM tracker_outbox WHERE state = 'pending' AND action = 'status' "
            "AND EXISTS (SELECT 1 FROM tracker_outbox AS p WHERE p.state = 'pending' "
            "AND p.ticket_id = tracker_outbox.ticket_id AND p.action = 'push')"
        )
        conn.execute("UPDATE tracker_sync SET last_error = NULL, failed_at = NULL WHERE id = 1")
        return cursor.rowcount


def defer(run_log: RunLog, action_id: int, until: datetime) -> None:
    """Retry later without counting a failure (the tracker's rate limit)."""
    with run_log.transaction() as tx:
        tx.conn.execute(
            "UPDATE tracker_outbox SET next_at = ? WHERE id = ?", (format_ts(until), action_id)
        )


def sync_state(run_log: RunLog) -> SyncState:
    with run_log._reading() as conn:
        pending = conn.execute(
            "SELECT COUNT(*) FROM tracker_outbox WHERE state = 'pending'"
        ).fetchone()[0]
        row = conn.execute(
            "SELECT last_error, last_synced_at, failed_at FROM tracker_sync WHERE id = 1"
        ).fetchone()
    return SyncState(int(pending), *(row or (None, None, None)))


def queued_keys(run_log: RunLog) -> set[str]:
    """Every ``once_key`` ever queued, for the dry run."""
    with run_log._reading() as conn:
        rows = conn.execute(
            "SELECT once_key FROM tracker_outbox WHERE once_key IS NOT NULL"
        ).fetchall()
    return {key for (key,) in rows}


def run_commit(run_log: RunLog, run_id: int) -> str | None:
    """The commit a run's work was integrated as, from its latest ``integrate`` event."""
    with run_log._reading() as conn:
        row = conn.execute(
            "SELECT json_extract(payload, '$.commit') FROM events "
            "WHERE run_id = ? AND kind = 'integrate' ORDER BY id DESC LIMIT 1",
            (run_id,),
        ).fetchone()
    return str(row[0]) if row and row[0] else None
