"""The run-history database: ``<workspace>/.spoolhq/state.db``.

Stdlib ``sqlite3`` only. Each connection runs in WAL mode with ``synchronous=NORMAL``,
foreign keys on and a 5 s busy timeout; ``isolation_level=None`` leaves transactions to
the caller (``BEGIN IMMEDIATE`` … ``COMMIT``). The schema is an ordered list of
migration scripts tracked by ``PRAGMA user_version``.
"""

import sqlite3
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path

STATE_DIR = ".spoolhq"
DB_FILE = "state.db"
BUSY_TIMEOUT_MS = 5000

Clock = Callable[[], datetime]

_V1 = """
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT,
    daemon_instance TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT
);

CREATE TABLE attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    ticket_id TEXT NOT NULL,
    number INTEGER NOT NULL,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    dir TEXT NOT NULL,
    backend TEXT,
    model TEXT,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cost_micro_usd INTEGER,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    UNIQUE (ticket_id, number)
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    attempt_id INTEGER REFERENCES attempts(id),
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL
);

CREATE TRIGGER events_no_update BEFORE UPDATE ON events
BEGIN
    SELECT RAISE(ABORT, 'events are append-only');
END;

CREATE TRIGGER events_no_delete BEFORE DELETE ON events
BEGIN
    SELECT RAISE(ABORT, 'events are append-only');
END;

CREATE INDEX runs_ticket_id ON runs (ticket_id);
CREATE INDEX runs_status ON runs (status);
CREATE INDEX attempts_run_id ON attempts (run_id);
CREATE INDEX events_run_id_id ON events (run_id, id);
"""

# The run loop (T13): the progress note for T14 and a paused run's usage-limit reset.
_V2 = """
ALTER TABLE runs ADD COLUMN progress_note TEXT;
ALTER TABLE runs ADD COLUMN reset_at TEXT;
"""

# Local integration (T14): the journal that makes merging into main crash-safe.
_V3 = """
CREATE TABLE integrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    ticket_id TEXT NOT NULL,
    default_branch TEXT NOT NULL,
    main_sha TEXT NOT NULL,
    commit_sha TEXT,
    state TEXT NOT NULL,
    started_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX integrations_state ON integrations (state);
"""

# Weighted token budget: the part of input_tokens read from the prompt cache.
_V4 = """
ALTER TABLE attempts ADD COLUMN cache_read_tokens INTEGER NOT NULL DEFAULT 0;
"""

# The planner (T15): a run is a ticket's run or the generation of a plan.
_V5 = """
ALTER TABLE runs ADD COLUMN kind TEXT NOT NULL DEFAULT 'ticket';
"""

# GitHub delivery (T17): the pull request a run's work was delivered as.
_V6 = """
ALTER TABLE runs ADD COLUMN pr_number INTEGER;
ALTER TABLE runs ADD COLUMN pr_url TEXT;
ALTER TABLE runs ADD COLUMN pr_branch TEXT;
"""

MIGRATIONS: tuple[str, ...] = (_V1, _V2, _V3, _V4, _V5, _V6)
"""Migration ``n`` (1-based) takes the database from version ``n - 1`` to ``n``."""

SCHEMA_VERSION = len(MIGRATIONS)

_NOT_A_DATABASE = frozenset({"SQLITE_NOTADB", "SQLITE_CORRUPT"})


class RunLogError(Exception):
    """``state.db`` cannot be used: not a SpoolHQ database, or a schema we can't handle."""


def state_dir(workspace: Path) -> Path:
    return workspace / STATE_DIR


def state_db_path(workspace: Path) -> Path:
    return state_dir(workspace) / DB_FILE


def utc_now() -> datetime:
    return datetime.now(UTC)


def format_ts(moment: datetime) -> str:
    """UTC ISO 8601 with milliseconds and ``Z``: ``2026-10-18T09:00:00.000Z``."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError(f"timestamps must be timezone-aware, got naive {moment.isoformat()}")
    utc = moment.astimezone(UTC)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{utc.microsecond // 1000:03d}Z"


def _statements(script: str) -> Iterator[str]:
    """Split a script into complete statements (trigger bodies included)."""
    buffer = ""
    for line in script.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            yield buffer.strip()
            buffer = ""
    if buffer.strip():
        raise ValueError(f"incomplete SQL statement in migration: {buffer.strip()!r}")


def _user_version(conn: sqlite3.Connection) -> int:
    version: int = conn.execute("PRAGMA user_version").fetchone()[0]
    return version


def _check_not_newer(version: int) -> None:
    if version > SCHEMA_VERSION:
        raise RunLogError(
            f"{DB_FILE}: schema version {version} is newer than this SpoolHQ supports "
            f"({SCHEMA_VERSION}); upgrade SpoolHQ."
        )


def _migrate(conn: sqlite3.Connection) -> None:
    conn.execute("BEGIN IMMEDIATE")
    try:
        # Read under the write lock, so two processes opening a new file don't both
        # run the same migration.
        version = _user_version(conn)
        _check_not_newer(version)
        for script in MIGRATIONS[version:]:
            for statement in _statements(script):
                conn.execute(statement)
        if version != SCHEMA_VERSION:
            # PRAGMA takes no parameters; SCHEMA_VERSION is a constant of this module.
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION:d}")
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise


def connect(workspace: Path, *, read_only: bool = False) -> sqlite3.Connection:
    """Open ``state.db``, migrating it to the current schema unless ``read_only``.

    ``.spoolhq/`` is created when missing. A read-only open never creates or changes
    the file (a missing file raises ``FileNotFoundError``) and refuses a database that
    has not been migrated yet. Raises RunLogError for a file that is not a SQLite
    database or has a schema newer than this code.
    """
    path = state_db_path(workspace)
    if read_only:
        if not path.is_file():
            raise FileNotFoundError(f"{path} does not exist")
        conn = sqlite3.connect(
            f"{path.resolve().as_uri()}?mode=ro",
            uri=True,
            isolation_level=None,
            check_same_thread=False,
        )
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    try:
        try:
            conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS:d}")
            if read_only:
                conn.execute("PRAGMA query_only = ON")
            else:
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA foreign_keys = ON")
            if read_only:
                version = _user_version(conn)
                _check_not_newer(version)
                if version < SCHEMA_VERSION:
                    raise RunLogError(
                        f"{DB_FILE}: schema version {version} is older than this SpoolHQ "
                        f"expects ({SCHEMA_VERSION}); start the daemon to upgrade it."
                    )
            else:
                _migrate(conn)
        except sqlite3.DatabaseError as exc:
            # Only a file that isn't (or is no longer) a database; a locked or
            # unreadable one keeps its own error.
            if exc.sqlite_errorname not in _NOT_A_DATABASE:
                raise
            raise RunLogError(f"{DB_FILE}: not a SpoolHQ database ({exc})") from exc
    except BaseException:
        conn.close()
        raise
    return conn
