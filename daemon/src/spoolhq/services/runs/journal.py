"""The integration journal: one row per attempt to merge a run into the default branch.

Each step of an integration writes its state here in its own committed transaction
before the next step starts, so startup recovery can tell how far a crashed
integration got (``docs/integration.md``).
"""

import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from spoolhq.services.runs.log import RunLog

COLUMNS = (
    "id, run_id, ticket_id, default_branch, main_sha, commit_sha, state, started_at, updated_at"
)


class IntegrationState(StrEnum):
    MERGING = "merging"
    """main is being merged into the worktree, gated and squashed; main is untouched."""
    COMMITTED = "committed"
    """The squash commit exists (``commit_sha``); main is untouched."""
    ADVANCED = "advanced"
    """The default branch points at ``commit_sha``."""
    TAGGED = "tagged"
    DONE = "done"
    ABANDONED = "abandoned"
    """Stopped before main moved (conflict, gates, a block, a wait); nothing to recover."""


OPEN_STATES = (
    IntegrationState.MERGING,
    IntegrationState.COMMITTED,
    IntegrationState.ADVANCED,
    IntegrationState.TAGGED,
)


@dataclass(frozen=True)
class Integration:
    id: int
    run_id: int
    ticket_id: str
    default_branch: str
    main_sha: str
    commit_sha: str | None
    state: IntegrationState
    started_at: str
    updated_at: str


def _to_integration(row: tuple[Any, ...]) -> Integration:
    return Integration(
        id=row[0],
        run_id=row[1],
        ticket_id=row[2],
        default_branch=row[3],
        main_sha=row[4],
        commit_sha=row[5],
        state=IntegrationState(row[6]),
        started_at=row[7],
        updated_at=row[8],
    )


def _get(conn: sqlite3.Connection, integration_id: int) -> Integration:
    row = conn.execute(
        f"SELECT {COLUMNS} FROM integrations WHERE id = ?",  # noqa: S608 - constant columns
        (integration_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"integration {integration_id} not found")
    return _to_integration(row)


def start_integration(
    run_log: RunLog, run_id: int, ticket_id: str, default_branch: str, main_sha: str
) -> Integration:
    """A new journal row in state ``merging``."""
    with run_log.transaction() as tx:
        now = tx.now()
        cursor = tx.conn.execute(
            "INSERT INTO integrations (run_id, ticket_id, default_branch, main_sha, state, "
            "started_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, ticket_id, default_branch, main_sha, IntegrationState.MERGING.value, now, now),
        )
        assert cursor.lastrowid is not None  # noqa: S101 - an INSERT always sets it
        return _get(tx.conn, cursor.lastrowid)


def set_integration_state(
    run_log: RunLog,
    integration_id: int,
    state: IntegrationState,
    *,
    commit_sha: str | None = None,
) -> Integration:
    """Record ``state`` (and ``commit_sha`` when given), committed before returning."""
    with run_log.transaction() as tx:
        tx.conn.execute(
            "UPDATE integrations SET state = ?, commit_sha = COALESCE(?, commit_sha), "
            "updated_at = ? WHERE id = ?",
            (IntegrationState(state).value, commit_sha, tx.now(), integration_id),
        )
        return _get(tx.conn, integration_id)


def open_integrations(run_log: RunLog) -> list[Integration]:
    """Integrations that neither finished nor were abandoned, oldest first."""
    with run_log.transaction() as tx:
        rows = tx.conn.execute(
            f"SELECT {COLUMNS} FROM integrations WHERE state IN (?, ?, ?, ?) ORDER BY id",  # noqa: S608 - constant columns
            tuple(state.value for state in OPEN_STATES),
        ).fetchall()
    return [_to_integration(row) for row in rows]


def last_integration(run_log: RunLog) -> Integration | None:
    """The integration that finished (``done``) most recently, if any."""
    with run_log.transaction() as tx:
        row = tx.conn.execute(
            f"SELECT {COLUMNS} FROM integrations WHERE state = ? "  # noqa: S608 - constant columns
            "ORDER BY updated_at DESC, id DESC LIMIT 1",
            (IntegrationState.DONE.value,),
        ).fetchone()
    return _to_integration(row) if row is not None else None
