"""Crash recovery: runs left active by a daemon that is no longer running.

Only the database changes here. Ticket file statuses are reconciled by the run loop
(T13) and worktrees are cleaned up by T08.
"""

from spoolhq.services.runs.log import RunLog, fetch_run
from spoolhq.services.runs.model import AttemptStatus, EventKind, Run, RunStatus

INTERRUPTED_REASON = "the daemon stopped while this run was active"
RECOVERABLE = (RunStatus.RUNNING, RunStatus.PAUSED)


def recover_interrupted(run_log: RunLog) -> list[Run]:
    """Mark ``running`` and ``paused`` runs of other daemon instances ``interrupted``.

    Their ``running`` attempts become ``interrupted`` too, and each run gets one
    ``run.interrupted`` event, all in one transaction. ``awaiting_approval`` and ended
    runs are untouched, as are the current instance's runs; a second call is a no-op.
    Callers must hold the daemon single-instance lock, so that the other instance is
    known to be gone.
    """
    with run_log.transaction() as tx:
        rows = tx.conn.execute(
            "SELECT id, status FROM runs WHERE status IN (?, ?) AND daemon_instance != ? "
            "ORDER BY id",
            (*(status.value for status in RECOVERABLE), run_log.daemon_instance),
        ).fetchall()
        if not rows:
            return []
        now = tx.now()
        recovered = []
        for run_id, previous in rows:
            attempt_ids = [
                attempt_id
                for (attempt_id,) in tx.conn.execute(
                    "SELECT id FROM attempts WHERE run_id = ? AND status = ? ORDER BY id",
                    (run_id, AttemptStatus.RUNNING.value),
                )
            ]
            tx.conn.execute(
                "UPDATE attempts SET status = ?, ended_at = ? WHERE run_id = ? AND status = ?",
                (AttemptStatus.INTERRUPTED.value, now, run_id, AttemptStatus.RUNNING.value),
            )
            tx.conn.execute(
                "UPDATE runs SET status = ?, reason = ?, ended_at = ? WHERE id = ?",
                (RunStatus.INTERRUPTED.value, INTERRUPTED_REASON, now, run_id),
            )
            tx.append_event(
                run_id,
                EventKind.RUN_INTERRUPTED,
                {
                    "from": previous,
                    "reason": INTERRUPTED_REASON,
                    "attempt_ids": attempt_ids,
                },
            )
            recovered.append(fetch_run(tx.conn, run_id))
    return recovered
