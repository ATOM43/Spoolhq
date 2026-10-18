# Runs

The run log is the record of everything the loop does: every run, every attempt inside it, and an append-only stream of events. It lives in the project workspace, next to the tickets, and survives daemon restarts. The run loop that drives it comes in T13; the WebSocket that streams events to the desktop app comes in T19.

The code is `services/runs/`: the database in `db.py`, `RunLog` in `log.py`, statuses and records in `model.py`, attempt files in `files.py`, the event bus in `bus.py`, crash recovery in `recovery.py` and the daemon's per-workspace registry in `registry.py`.

## Runs and attempts

A **run** is one execution of the loop for one ticket, from being picked until it ends.

| Status | Meaning |
| --- | --- |
| `running` | The loop is working on the ticket. |
| `paused` | Waiting for a subscription usage-limit reset. |
| `awaiting_approval` | A PR or local approval is pending. Survives restarts. |
| `done` | Finished and merged. Terminal. |
| `blocked` | Stopped; a person has to step in. Terminal. |
| `cancelled` | Stopped on request. Terminal. |
| `interrupted` | The daemon stopped while the run was active (see [Recovery](#recovery)). Terminal. |

A terminal status sets `ended_at`, and a run that has ended can't change again: `set_run_status` raises `run 12 is already done`, and `start_attempt` refuses it too.

An **attempt** is one implementer pass inside a run, together with its gates and review.

- Kinds: `initial`, `gate_retry`, `review_retry`, `conflict_retry`, `pr_changes`.
- Statuses: `running`, then one of `gates_failed`, `changes_requested`, `approved`, `needs_human`, `conflict`, `error`, `cancelled`, `interrupted`. `finish_attempt` ends a `running` attempt and sets `ended_at`; an attempt finishes once.
- Numbers count **per ticket, across all its runs**: T04's first run has attempts 1 and 2, its second run starts at 3. A different ticket starts again at 1.
- Usage: `record_usage(attempt_id, input_tokens, output_tokens, cost_micro_usd=None)` adds to the attempt's totals. Cost is an integer number of micro-USD (1 USD = 1 000 000); a `None` cost leaves the stored cost unchanged, and a stored `NULL` plus a value becomes that value. Negative numbers raise `ValueError`. `run_usage(run_id)` sums a run's attempts; its cost is `None` if no attempt reported one.

## The database

`<workspace>/.spoolhq/state.db`, created (with `.spoolhq/`) the first time a `RunLog` opens the workspace. It is stdlib `sqlite3`, no ORM.

- Every connection sets `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON` and `busy_timeout=5000`. A committed transaction survives a crash of the process; a power loss can drop the last few transactions.
- One connection per `RunLog`, opened with `check_same_thread=False` and guarded by a lock, so a `RunLog` can be shared between threads. `isolation_level=None`: each method is one explicit `BEGIN IMMEDIATE` … `COMMIT`.
- **Migrations** are an ordered list of SQL scripts in `db.py`, tracked by `PRAGMA user_version`; opening a database runs the scripts it is missing, inside one transaction. This version of SpoolHQ ships schema version 1.
- A database newer than the code is refused: `state.db: schema version 3 is newer than this SpoolHQ supports (1); upgrade SpoolHQ.`
- A file that isn't a SQLite database is refused: `state.db: not a SpoolHQ database (file is not a database)`.
- All SQL takes its values as parameters; ticket text and agent output never become SQL.

### Schema (version 1)

```sql
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT,
    daemon_instance TEXT NOT NULL,   -- the daemon that started the run
    started_at TEXT NOT NULL,
    ended_at TEXT
);

CREATE TABLE attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    ticket_id TEXT NOT NULL,
    number INTEGER NOT NULL,         -- per ticket: 1, 2, 3, ...
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    dir TEXT NOT NULL,               -- relative to the workspace: runs/T04/003
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
    payload TEXT NOT NULL            -- JSON object
);
```

Triggers `BEFORE UPDATE` and `BEFORE DELETE` on `events` raise `events are append-only`, so not even a hand-written statement can change history. Indexes: `runs(ticket_id)`, `runs(status)`, `attempts(run_id)`, `events(run_id, id)`.

Timestamps are UTC ISO 8601 with milliseconds and `Z`, like `2026-10-18T09:00:00.000Z`. They come from the `RunLog`'s `clock` (default `datetime.now(UTC)`); a clock that returns a naive datetime raises `ValueError`.

## Attempt folders

Each attempt has a folder, created by `start_attempt` with the row:

```text
<workspace>/runs/
  T04/
    001/
      transcript.jsonl   # one JSON object per line (append_transcript)
      gates.json         # gate results
      diff.patch         # the attempt's diff
      review.json        # the reviewer's verdict
    002/
  T05/
    001/
```

- The folder is `runs/<ticket>/<NNN>` (three digits, zero-padded), stored in the row's `dir` relative to the workspace, so the row alone finds the files. The ticket id is checked against the ticket id pattern (`T` + 2–3 digits) before it is used in a path.
- Only the four names above can be written; any other name (including anything with `/`, `\` or `..`) raises `ValueError`. `write_artifact` writes atomically (a temp file in the same folder, then `os.replace`); `append_transcript` appends one line and `fsync`s it.
- `attempt_files(workspace, attempt)` returns the allowed files that exist. A `dir` that resolves outside `<workspace>/runs/` (an edited `../../etc`, an absolute path, a symlink pointing out) raises `ValueError`.
- If the daemon dies between creating the folder and committing the row, the empty folder is reused by the next attempt with that number; a folder that already has files is never reused (`FileExistsError`).

## Events

Every lifecycle change appends its event in the same transaction:

| Kind | Written by | Payload |
| --- | --- | --- |
| `run.started` | `start_run` | `{"ticket_id"}` |
| `run.status` | `set_run_status` | `{"from", "to", "reason"}` |
| `run.interrupted` | `recover_interrupted` | `{"from", "reason", "attempt_ids"}` |
| `attempt.started` | `start_attempt` | `{"number", "kind", "dir", "backend", "model"}` |
| `attempt.finished` | `finish_attempt` | `{"number", "status"}` |
| `agent.message`, `agent.tool_call`, `agent.file_edit`, `agent.usage`, `gate.result`, `review.verdict`, `log` | `append_event` (the run loop) | free-form |

- Ids increase across the whole workspace, so `events_since(after_id, run_id=None, limit=1000)` is a cursor.
- A payload must be a JSON-serialisable `dict` (no sets, no `NaN`). Its compact UTF-8 encoding is capped at **64 KiB** (65 536 bytes); a larger one raises `ValueError` naming its size. Large content (transcripts, diffs, gate output) belongs in the attempt's files.

## The event bus

`EventBus` is an in-process, synchronous, thread-safe fan-out with no database access; the daemon keeps one per workspace. `RunLog` publishes each operation's events **after its transaction commits**, in id order; a transaction that fails publishes nothing. `publish` never blocks and never raises.

```python
with bus.subscribe(run_id=None, maxsize=1000) as sub:
    event = sub.get(timeout=1.0)   # Event, or None on timeout
    sub.last_id                    # id of the last event get() returned
    sub.lagged                     # True once the queue overflowed
```

**Lag and resync contract** (T19 relies on this):

1. Each subscription has a bounded queue (`maxsize`, default 1000). `publish` only appends to it.
2. When the queue is full, the subscription is marked `lagged` and **receives no further events**. The events already queued stay and can still be read.
3. `get` returns `None` at once when nothing is queued and the subscription is lagged or closed, so a consumer never waits for events that will not come.
4. `last_id` is the id of the last event `get` returned; before the first `get`, the id of the last event the bus had published when the subscription started. Every event after `last_id` is either still queued or in the database.
5. A lagged consumer resyncs from the database: `run_log.events_since(sub.last_id, run_id=...)` (in pages of `limit`), then `subscribe` again. Events can then arrive both from the database read and the new queue; skip any whose id is not above the last id handled.
6. To start a stream from a client's cursor without a gap: subscribe first, read `events_since(cursor)`, then read the queue, skipping ids already sent.

`subscribe(..., notify=callback)` calls `callback(sub)` on the publishing thread after an event is queued or the subscription becomes lagged, so an asyncio consumer can wake its loop with `loop.call_soon_threadsafe` instead of a thread per subscriber. The callback must be quick and must not call the bus or the run log.

A subscriber's callback or queue error never reaches the publisher or other subscribers: it is logged, and that subscription is marked `lagged` (and resyncs like any other).

## Recovery

`recover_interrupted(run_log)` closes what a stopped daemon left behind, in one transaction:

- Every run in `running` or `paused` whose `daemon_instance` is not the current one becomes `interrupted`, with `ended_at` set and the reason `the daemon stopped while this run was active`. Each gets exactly one `run.interrupted` event.
- Every `running` attempt of those runs becomes `interrupted`, with `ended_at` set.
- `awaiting_approval`, `done`, `blocked` and `cancelled` runs are untouched (approval survives restarts), and so are the current daemon's own runs.
- A second call finds nothing and adds no events.

Recovery touches only the database. Reconciling the ticket files' statuses is the run loop's job (T13), and removing leftover worktrees is T08's.

The daemon runs recovery at startup, for every workspace under the projects folder (`projects_dir`), under a fresh `daemon_instance` (`uuid4().hex`). A workspace whose `state.db` can't be opened is logged as an error with its path and skipped; it doesn't stop startup. Each recovered run gets one log line (`run interrupted by a daemon restart`, with project, run id and ticket). The open `RunLog` and `EventBus` of every workspace are kept in `app.state.runs` and closed on shutdown.

## The single-instance lock

Recovery assumes that a run from another `daemon_instance` has no live daemon behind it. `spool serve` makes that true: before uvicorn starts, it takes an exclusive OS lock on `~/.spoolhq/daemon.lock` (`fcntl.flock` on POSIX, `msvcrt.locking` on Windows) and writes its pid into the file. The lock is held until the daemon exits, and the OS releases it when the process dies, so a crashed daemon never leaves a stale lock.

A second `spool serve` exits with status 1:

```text
error: another SpoolHQ daemon is already running (pid 4242)
```

(`pid unknown` if the file has no readable pid.)

## Reading runs from the CLI

```sh
spool runs list <project> [--ticket T04] [--limit 50]   # id, ticket, status, started, attempts, tokens; newest first
spool runs show <project> <run_id>                      # the run, then its attempts with usage and folder
```

Like `spool tickets` and `spool plan`, these call the service directly, so the daemon need not be running. They open `state.db` read-only (`file:…?mode=ro`, `query_only`), so they never migrate, never run recovery and never change anything; a project with no `state.db` yet has no runs. An unknown project or run exits 1 with a one-line message (`error: run 99 not found`).
