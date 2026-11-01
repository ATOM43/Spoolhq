"""Run history, newest first, a page at a time behind an opaque cursor.

The cursor encodes the last run of a page (``started_at`` and ``id``); the next page
holds the runs strictly older than it in ``(started_at, id)`` order. A run started while
a client pages sorts before every cursor, so it never shows up twice.
"""

import base64
import binascii
from dataclasses import dataclass

from spoolhq.services.runs.log import RunLog
from spoolhq.services.runs.model import Run
from spoolhq.services.runs.rows import RUN_COLUMNS, to_run


@dataclass(frozen=True)
class RunPage:
    runs: list[Run]
    next_cursor: str | None
    """None on the last page."""


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


def page_runs(run_log: RunLog, cursor: str | None, limit: int) -> RunPage:
    """Up to ``limit`` runs older than ``cursor`` (the newest ones without it)."""
    started_at, run_id = decode_cursor(cursor) if cursor else ("￿", 0)
    with run_log._reading() as conn:
        rows = conn.execute(
            f"SELECT {RUN_COLUMNS} FROM runs "  # noqa: S608 - constant columns
            "WHERE started_at < ? OR (started_at = ? AND id < ?) "
            "ORDER BY started_at DESC, id DESC LIMIT ?",
            (started_at, started_at, run_id, limit + 1),
        ).fetchall()
    runs = [to_run(row) for row in rows[:limit]]
    more = len(rows) > limit
    return RunPage(runs, encode_cursor(runs[-1]) if more else None)
