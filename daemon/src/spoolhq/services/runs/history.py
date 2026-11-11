"""Run history, newest first, a page at a time behind an opaque cursor; and a run's
stored events, oldest first, a page at a time (``page_events``).

The cursor encodes the last run of a page (``started_at`` and ``id``); the next page
holds the runs strictly older than it in ``(started_at, id)`` order. A run started while
a client pages sorts before every cursor, so it never shows up twice.
"""

import base64
import binascii
from dataclasses import dataclass

from spoolhq.services.runs.log import RunLog
from spoolhq.services.runs.model import Event, EventKind, Run, RunKind
from spoolhq.services.runs.rows import EVENT_COLUMNS, RUN_COLUMNS, to_event, to_run


@dataclass(frozen=True)
class RunStats:
    """A run's attempts summed up, for a row of the past-runs table."""

    attempts: int = 0
    last_attempt: int | None = None
    """The newest attempt's number (per ticket), which its replay opens."""
    backend: str | None = None
    """The newest attempt's backend."""
    tokens: int = 0
    """Input and output tokens of the attempts that reported no cost (subscriptions)."""
    cost_micro_usd: int | None = None
    """The cost summed over the attempts that reported one; None when none did."""


@dataclass(frozen=True)
class RunPage:
    runs: list[Run]
    next_cursor: str | None
    """None on the last page."""
    stats: dict[int, RunStats]
    """By run id; a run with no attempt has no entry."""


def encode_cursor(run: Run) -> str:
    raw = f"{run.started_at}|{run.id}".encode()
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> tuple[str, int]:
    """``(started_at, run_id)``; ValueError for anything ``encode_cursor`` didn't make."""
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode("ascii")
        started_at, _, run_id = raw.rpartition("|")
        if not started_at:
            raise ValueError
        return started_at, int(run_id)
    except (binascii.Error, UnicodeDecodeError, ValueError):
        raise ValueError(f"invalid cursor {cursor[:40]!r}") from None


def page_runs(
    run_log: RunLog, cursor: str | None, limit: int, kind: RunKind | None = None
) -> RunPage:
    """Up to ``limit`` runs older than ``cursor`` (the newest ones without it), only
    those of ``kind`` when given."""
    started_at, run_id = decode_cursor(cursor) if cursor else ("￿", 0)
    wanted = kind.value if kind else None
    with run_log._reading() as conn:
        rows = conn.execute(
            f"SELECT {RUN_COLUMNS} FROM runs "  # noqa: S608 - constant columns
            "WHERE (started_at < ? OR (started_at = ? AND id < ?)) AND (? IS NULL OR kind = ?) "
            "ORDER BY started_at DESC, id DESC LIMIT ?",
            (started_at, started_at, run_id, wanted, wanted, limit + 1),
        ).fetchall()
        runs = [to_run(row) for row in rows[:limit]]
        marks = ",".join("?" * len(runs))
        # SQLite takes a bare column (backend) from the row that holds MAX(number).
        sums = conn.execute(
            "SELECT run_id, COUNT(*), MAX(number), backend, "  # noqa: S608 - only "?" marks
            "SUM(CASE WHEN cost_micro_usd IS NULL THEN input_tokens + output_tokens ELSE 0 END), "
            f"SUM(cost_micro_usd) FROM attempts WHERE run_id IN ({marks}) GROUP BY run_id",
            [run.id for run in runs],
        ).fetchall()
    more = len(rows) > limit
    stats = {int(row[0]): RunStats(*row[1:]) for row in sums}
    return RunPage(runs, encode_cursor(runs[-1]) if more else None, stats)


@dataclass(frozen=True)
class EventPage:
    events: list[Event]
    next_after: int | None
    """The ``after`` of the next page; None on the last page."""
    total: int
    """Every event of the run (or of the attempt's window), whatever ``after`` is."""


def page_events(
    run_log: RunLog, run_id: int, attempt: int | None, after: int, limit: int
) -> EventPage:
    """A run's events after ``after``, oldest first, at most ``limit``.

    With ``attempt`` (its number), only what happened from that attempt's start until the
    next attempt's start: its run-level events (the worktree, the integration, the end of
    the run) included, the worktree for the run's first attempt. KeyError for an unknown
    run or attempt.
    """
    attempts = run_log.list_attempts(run_id)
    start, high = 0, None
    if attempt is not None:
        index = next(i for i, a in enumerate(attempts) if a.number == attempt)  # StopIteration
        bounds = _starts(run_log, run_id)
        if index > 0:
            start = bounds[attempts[index].id] - 1
        if index + 1 < len(attempts):
            high = bounds[attempts[index + 1].id]
    window = "run_id = ? AND id > ? AND (? IS NULL OR id < ?)"
    with run_log._reading() as conn:
        rows = conn.execute(
            f"SELECT {EVENT_COLUMNS} FROM events WHERE {window} ORDER BY id LIMIT ?",  # noqa: S608 - constants
            (run_id, max(after, start), high, high, limit + 1),
        ).fetchall()
        total = conn.execute(
            f"SELECT COUNT(*) FROM events WHERE {window}",  # noqa: S608 - constant
            (run_id, start, high, high),
        ).fetchone()[0]
    events = [to_event(row) for row in rows[:limit]]
    return EventPage(events, events[-1].id if len(rows) > limit else None, total)


def _starts(run_log: RunLog, run_id: int) -> dict[int, int]:
    """Each attempt's id → the seq of its ``attempt.started`` event."""
    with run_log._reading() as conn:
        rows = conn.execute(
            "SELECT attempt_id, MIN(id) FROM events WHERE run_id = ? AND kind = ? "
            "GROUP BY attempt_id",
            (run_id, EventKind.ATTEMPT_STARTED.value),
        ).fetchall()
    return {int(attempt_id): int(seq) for attempt_id, seq in rows}
