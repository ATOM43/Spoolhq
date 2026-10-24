"""The run log: schema, append-only events, numbering, lifecycle, usage and payloads."""

import json
import sqlite3
import threading
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from spoolhq.services.runs import (
    MAX_PAYLOAD_BYTES,
    SCHEMA_VERSION,
    AttemptKind,
    AttemptStatus,
    EventBus,
    EventKind,
    RunLog,
    RunLogError,
    RunStatus,
    db,
    format_ts,
    recover_interrupted,
    state_db_path,
)
from tests.conftest import FixedClock


@pytest.fixture
def run_log(workspace: Path, clock: FixedClock) -> Iterator[RunLog]:
    with RunLog(workspace, clock=clock, daemon_instance="A") as log:
        yield log


def raw(workspace: Path) -> sqlite3.Connection:
    return sqlite3.connect(state_db_path(workspace), isolation_level=None)


# Schema -------------------------------------------------------------------------------


def test_fresh_database_has_version_4_and_all_tables(workspace: Path) -> None:
    assert not (workspace / ".spoolhq").exists()
    with RunLog(workspace, daemon_instance="A"):
        pass

    conn = raw(workspace)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION == 4
        tables = {
            name for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        assert {"runs", "attempts", "events", "integrations"} <= tables
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        indexes = {
            name for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
        }
        assert {"runs_ticket_id", "runs_status", "attempts_run_id", "events_run_id_id"} <= indexes
    finally:
        conn.close()


def test_opening_twice_is_idempotent(workspace: Path) -> None:
    with RunLog(workspace, daemon_instance="A") as log:
        log.start_run("T04")
    with RunLog(workspace, daemon_instance="A") as log:
        assert [run.ticket_id for run in log.list_runs()] == ["T04"]
    conn = raw(workspace)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 4
    finally:
        conn.close()


def test_newer_schema_is_refused(workspace: Path) -> None:
    with RunLog(workspace, daemon_instance="A"):
        pass
    conn = raw(workspace)
    conn.execute("PRAGMA user_version = 5")
    conn.close()

    with pytest.raises(RunLogError) as info:
        RunLog(workspace, daemon_instance="A")
    assert str(info.value) == (
        "state.db: schema version 5 is newer than this SpoolHQ supports (4); upgrade SpoolHQ."
    )
    with pytest.raises(RunLogError, match="schema version 5 is newer"):
        RunLog.open_read_only(workspace)


def test_text_file_is_not_a_spoolhq_database(workspace: Path) -> None:
    path = state_db_path(workspace)
    path.parent.mkdir()
    path.write_text("these are not the runs you are looking for\n" * 20, encoding="utf-8")

    with pytest.raises(RunLogError) as info:
        RunLog(workspace, daemon_instance="A")
    assert str(info.value) == "state.db: not a SpoolHQ database (file is not a database)"


def test_read_only_open_of_a_missing_database_creates_nothing(workspace: Path) -> None:
    with pytest.raises(FileNotFoundError):
        RunLog.open_read_only(workspace)
    assert not (workspace / ".spoolhq").exists()


def test_read_only_open_refuses_an_unmigrated_database(workspace: Path) -> None:
    path = state_db_path(workspace)
    path.parent.mkdir()
    sqlite3.connect(path).close()
    path.write_bytes(b"")
    with pytest.raises(RunLogError, match="schema version 0 is older"):
        RunLog.open_read_only(workspace)


def test_read_only_log_refuses_writes(run_log: RunLog, workspace: Path) -> None:
    run = run_log.start_run("T04")
    with RunLog.open_read_only(workspace) as reader:
        assert reader.get_run(run.id) == run
        with pytest.raises(ValueError, match="read-only"):
            reader.start_run("T04")


def test_closed_log_refuses_calls(workspace: Path) -> None:
    log = RunLog(workspace, daemon_instance="A")
    log.close()
    log.close()
    with pytest.raises(ValueError, match="closed"):
        log.list_runs()


def test_daemon_instance_must_not_be_empty(workspace: Path) -> None:
    with pytest.raises(ValueError, match="daemon_instance"):
        RunLog(workspace, daemon_instance="")


# Append-only events -------------------------------------------------------------------


@pytest.mark.parametrize(
    "statement", ["UPDATE events SET kind = 'log'", "DELETE FROM events WHERE id = 1"]
)
def test_events_are_append_only(run_log: RunLog, workspace: Path, statement: str) -> None:
    run = run_log.start_run("T04")
    run_log.append_event(run.id, EventKind.LOG, {"msg": "hello"})
    conn = raw(workspace)
    try:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute(statement)
    finally:
        conn.close()
    assert len(run_log.events_since(0)) == 2


# Attempt numbering --------------------------------------------------------------------


def test_attempt_numbers_count_per_ticket_across_runs(run_log: RunLog, workspace: Path) -> None:
    run_a = run_log.start_run("T04")
    first = run_log.start_attempt(run_a.id, AttemptKind.INITIAL)
    second = run_log.start_attempt(run_a.id, AttemptKind.GATE_RETRY)
    run_log.set_run_status(run_a.id, RunStatus.BLOCKED, "gates keep failing")
    run_b = run_log.start_run("T04")
    third = run_log.start_attempt(run_b.id, AttemptKind.INITIAL)
    other = run_log.start_attempt(run_log.start_run("T05").id, "initial")

    assert [a.number for a in (first, second, third)] == [1, 2, 3]
    assert [a.dir for a in (first, second, third)] == [
        "runs/T04/001",
        "runs/T04/002",
        "runs/T04/003",
    ]
    for attempt in (first, second, third, other):
        assert (workspace / attempt.dir).is_dir()
    assert other.number == 1
    assert other.dir == "runs/T05/001"
    assert [a.number for a in run_log.list_attempts(run_a.id)] == [1, 2]
    assert [a.number for a in run_log.list_attempts(run_b.id)] == [3]


def test_existing_attempt_folder_with_files_is_refused(run_log: RunLog, workspace: Path) -> None:
    run = run_log.start_run("T04")
    folder = workspace / "runs" / "T04" / "001"
    folder.mkdir(parents=True)
    (folder / "diff.patch").write_text("someone else's\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        run_log.start_attempt(run.id, AttemptKind.INITIAL)
    assert run_log.list_attempts(run.id) == []
    assert [e.kind for e in run_log.events_since(0)] == [EventKind.RUN_STARTED]


def test_empty_folder_left_by_an_uncommitted_attempt_is_reused(
    run_log: RunLog, workspace: Path
) -> None:
    run = run_log.start_run("T04")
    (workspace / "runs" / "T04" / "001").mkdir(parents=True)

    attempt = run_log.start_attempt(run.id, AttemptKind.INITIAL)

    assert attempt.dir == "runs/T04/001"
    assert (workspace / attempt.dir).is_dir()


class FailingCommit:
    """Wraps a connection so that COMMIT fails, as on a full disk."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def execute(self, sql: str, *args: object) -> sqlite3.Cursor:
        if sql == "COMMIT":
            raise sqlite3.OperationalError("database or disk is full")
        return self.conn.execute(sql, *args)  # type: ignore[arg-type]

    def __getattr__(self, name: str) -> object:
        return getattr(self.conn, name)


def test_failed_commit_removes_the_attempt_folder(run_log: RunLog, workspace: Path) -> None:
    run = run_log.start_run("T04")
    bus = EventBus()
    run_log.bus = bus
    conn = run_log._conn
    assert conn is not None
    run_log._conn = FailingCommit(conn)  # type: ignore[assignment]
    with bus.subscribe() as sub:
        with pytest.raises(sqlite3.OperationalError, match="disk is full"):
            run_log.start_attempt(run.id, AttemptKind.INITIAL)
        assert sub.get(timeout=0) is None
    run_log._conn = conn
    assert run_log.list_attempts(run.id) == []
    assert not (workspace / "runs" / "T04" / "001").exists()
    assert run_log.start_attempt(run.id, AttemptKind.INITIAL).number == 1


def test_invalid_ticket_ids_never_reach_a_path(run_log: RunLog, workspace: Path) -> None:
    for bad in ("../T04", "T04/..", "t04", "T4", ""):
        with pytest.raises(ValueError, match="invalid ticket id"):
            run_log.start_run(bad)
    with pytest.raises(ValueError, match="invalid ticket id"):
        run_log.list_runs(ticket_id="../x")
    assert run_log.list_runs() == []


# Lifecycle ----------------------------------------------------------------------------


def test_run_lifecycle(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    assert run.status is RunStatus.RUNNING
    assert run.started_at == "2026-10-18T09:00:00.000Z"
    assert run.ended_at is None
    assert run.daemon_instance == "A"

    done = run_log.set_run_status(run.id, RunStatus.DONE)
    assert done.status is RunStatus.DONE
    assert done.ended_at is not None

    with pytest.raises(ValueError, match="run 1 is already done"):
        run_log.set_run_status(run.id, "running")

    events = run_log.events_since(0)
    assert [e.kind for e in events] == [EventKind.RUN_STARTED, EventKind.RUN_STATUS]
    assert events[1].payload == {"from": "running", "to": "done", "reason": None}
    assert all(e.run_id == run.id for e in events)


def test_non_terminal_status_keeps_the_run_open(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    paused = run_log.set_run_status(run.id, RunStatus.PAUSED, "usage limit, resets 14:00")
    assert paused.ended_at is None
    assert paused.reason == "usage limit, resets 14:00"
    waiting = run_log.set_run_status(run.id, RunStatus.AWAITING_APPROVAL)
    assert waiting.ended_at is None
    assert run_log.get_run(run.id) == waiting


def test_attempt_lifecycle(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    attempt = run_log.start_attempt(run.id, AttemptKind.INITIAL, backend="claude", model="m")
    assert attempt.status is AttemptStatus.RUNNING
    assert (attempt.backend, attempt.model) == ("claude", "m")
    assert attempt.ended_at is None

    finished = run_log.finish_attempt(attempt.id, AttemptStatus.GATES_FAILED)
    assert finished.status is AttemptStatus.GATES_FAILED
    assert finished.ended_at is not None
    assert run_log.get_attempt(attempt.id) == finished

    with pytest.raises(ValueError, match="attempt 1 is already gates_failed"):
        run_log.finish_attempt(attempt.id, AttemptStatus.APPROVED)
    with pytest.raises(ValueError, match="cannot finish as running"):
        run_log.finish_attempt(attempt.id, AttemptStatus.RUNNING)

    events = run_log.events_since(0)
    assert [e.kind for e in events] == [
        EventKind.RUN_STARTED,
        EventKind.ATTEMPT_STARTED,
        EventKind.ATTEMPT_FINISHED,
    ]
    assert events[1].attempt_id == attempt.id
    assert events[1].payload["dir"] == "runs/T04/001"
    assert events[2].payload == {"number": 1, "status": "gates_failed"}


def test_ended_run_takes_no_attempts(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    run_log.set_run_status(run.id, RunStatus.CANCELLED)
    with pytest.raises(ValueError, match="run 1 is already cancelled"):
        run_log.start_attempt(run.id, AttemptKind.INITIAL)


def test_unknown_ids_raise_key_error(run_log: RunLog) -> None:
    with pytest.raises(KeyError, match="run 12 not found"):
        run_log.get_run(12)
    with pytest.raises(KeyError, match="run 12 not found"):
        run_log.set_run_status(12, RunStatus.DONE)
    with pytest.raises(KeyError, match="run 12 not found"):
        run_log.list_attempts(12)
    with pytest.raises(KeyError, match="run 12 not found"):
        run_log.run_usage(12)
    with pytest.raises(KeyError, match="run 12 not found"):
        run_log.start_attempt(12, AttemptKind.INITIAL)
    with pytest.raises(KeyError, match="attempt 7 not found"):
        run_log.finish_attempt(7, AttemptStatus.ERROR)
    with pytest.raises(KeyError, match="attempt 7 not found"):
        run_log.record_usage(7, 1, 1)
    with pytest.raises(KeyError, match="attempt 7 not found"):
        run_log.get_attempt(7)


def test_unknown_status_and_kind_values_raise(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    with pytest.raises(ValueError):
        run_log.set_run_status(run.id, "finished")
    with pytest.raises(ValueError):
        run_log.start_attempt(run.id, "second_try")
    with pytest.raises(ValueError, match="unknown event kind"):
        run_log.append_event(run.id, "agent.thought", {})


def test_list_runs_is_newest_first_and_filters(run_log: RunLog) -> None:
    ids = [run_log.start_run(ticket).id for ticket in ("T04", "T05", "T04")]
    assert [r.id for r in run_log.list_runs()] == list(reversed(ids))
    assert [r.id for r in run_log.list_runs(ticket_id="T04")] == [ids[2], ids[0]]
    assert [r.id for r in run_log.list_runs(limit=1)] == [ids[2]]


def test_events_since_filters_by_run_and_limit(run_log: RunLog) -> None:
    a = run_log.start_run("T04")
    b = run_log.start_run("T05")
    for i in range(3):
        run_log.append_event(a.id, EventKind.LOG, {"i": i})
        run_log.append_event(b.id, EventKind.LOG, {"i": i})
    everything = run_log.events_since(0)
    assert [e.id for e in everything] == sorted(e.id for e in everything)
    assert len(everything) == 8
    only_b = run_log.events_since(0, run_id=b.id)
    assert {e.run_id for e in only_b} == {b.id}
    assert len(only_b) == 4
    assert [e.id for e in run_log.events_since(everything[2].id, limit=2)] == [
        everything[3].id,
        everything[4].id,
    ]


def test_event_with_an_attempt_of_another_run_is_refused(run_log: RunLog) -> None:
    a = run_log.start_run("T04")
    b = run_log.start_run("T05")
    attempt = run_log.start_attempt(a.id, AttemptKind.INITIAL)
    with pytest.raises(ValueError, match="belongs to run 1"):
        run_log.append_event(b.id, EventKind.LOG, {}, attempt_id=attempt.id)
    event = run_log.append_event(a.id, EventKind.AGENT_MESSAGE, {"t": 1}, attempt_id=attempt.id)
    assert event.attempt_id == attempt.id


# Timestamps ---------------------------------------------------------------------------


def test_naive_clock_raises(workspace: Path) -> None:
    with RunLog(workspace, clock=datetime.now, daemon_instance="A") as log:
        with pytest.raises(ValueError, match="naive"):
            log.start_run("T04")
        assert log.list_runs() == []


def test_timestamps_are_utc_with_milliseconds() -> None:
    moment = datetime(2026, 10, 18, 11, 0, 0, 123456, tzinfo=timezone(timedelta(hours=2)))
    assert format_ts(moment) == "2026-10-18T09:00:00.123Z"


# Usage --------------------------------------------------------------------------------


def test_usage_adds_up(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    first = run_log.start_attempt(run.id, AttemptKind.INITIAL)
    assert first.cost_micro_usd is None

    run_log.record_usage(first.id, 100, 50, 1500)
    updated = run_log.record_usage(first.id, 20, 5, None)
    assert (updated.input_tokens, updated.output_tokens, updated.cost_micro_usd) == (120, 55, 1500)

    second = run_log.start_attempt(run.id, AttemptKind.GATE_RETRY)
    run_log.record_usage(second.id, 10, 10, 500)
    usage = run_log.run_usage(run.id)
    assert (usage.input_tokens, usage.output_tokens, usage.cost_micro_usd) == (130, 65, 2000)
    assert usage.total_tokens == 195


def test_cache_reads_count_a_tenth_toward_weighted_tokens(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    attempt = run_log.start_attempt(run.id, AttemptKind.INITIAL)
    run_log.record_usage(attempt.id, 1000, 100, cache_read_tokens=900)
    stored = run_log.record_usage(attempt.id, 100, 0, cache_read_tokens=50)
    assert stored.cache_read_tokens == 950

    usage = run_log.run_usage(run.id)
    assert (usage.total_tokens, usage.cache_read_tokens) == (1200, 950)
    assert usage.weighted_tokens == 1200 - 950 + 95


def test_more_cache_reads_than_input_raise(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    attempt = run_log.start_attempt(run.id, AttemptKind.INITIAL)
    with pytest.raises(ValueError, match="part of input_tokens"):
        run_log.record_usage(attempt.id, 10, 0, cache_read_tokens=11)
    assert run_log.get_attempt(attempt.id).cache_read_tokens == 0


def test_usage_without_any_cost_stays_null(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    attempt = run_log.start_attempt(run.id, AttemptKind.INITIAL)
    assert run_log.record_usage(attempt.id, 1, 2).cost_micro_usd is None
    usage = run_log.run_usage(run.id)
    assert (usage.input_tokens, usage.output_tokens, usage.cost_micro_usd) == (1, 2, None)
    empty = run_log.run_usage(run_log.start_run("T05").id)
    assert (empty.input_tokens, empty.output_tokens, empty.cost_micro_usd) == (0, 0, None)


@pytest.mark.parametrize(
    ("tokens_in", "tokens_out", "cost"),
    [(-1, 0, None), (0, -1, None), (0, 0, -1), (1.5, 0, None), (True, 0, None)],
)
def test_bad_usage_numbers_raise(
    run_log: RunLog, tokens_in: int, tokens_out: int, cost: int | None
) -> None:
    run = run_log.start_run("T04")
    attempt = run_log.start_attempt(run.id, AttemptKind.INITIAL)
    with pytest.raises(ValueError):
        run_log.record_usage(attempt.id, tokens_in, tokens_out, cost)
    stored = run_log.get_attempt(attempt.id)
    assert (stored.input_tokens, stored.output_tokens, stored.cost_micro_usd) == (0, 0, None)


# Payloads -----------------------------------------------------------------------------

EMPTY_STRING_PAYLOAD = len(json.dumps({"x": ""}, separators=(",", ":")))


def test_payload_over_the_limit_raises_with_its_size(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    payload = {"x": "a" * (MAX_PAYLOAD_BYTES + 1 - EMPTY_STRING_PAYLOAD)}
    with pytest.raises(ValueError, match=f"{MAX_PAYLOAD_BYTES + 1} bytes"):
        run_log.append_event(run.id, EventKind.LOG, payload)


def test_payload_at_the_limit_is_stored(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    payload = {"x": "a" * (MAX_PAYLOAD_BYTES - EMPTY_STRING_PAYLOAD)}
    event = run_log.append_event(run.id, EventKind.LOG, payload)
    assert run_log.events_since(event.id - 1)[0].payload == payload


def test_payload_size_counts_utf8_bytes(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    payload = {"x": "é" * (MAX_PAYLOAD_BYTES // 2)}
    with pytest.raises(ValueError, match="bytes, over the"):
        run_log.append_event(run.id, EventKind.LOG, payload)


@pytest.mark.parametrize(
    "payload", [{"x": {1, 2}}, {"x": float("nan")}, ["not", "a", "dict"], "text", None]
)
def test_non_json_payloads_raise(run_log: RunLog, payload: object) -> None:
    run = run_log.start_run("T04")
    with pytest.raises(ValueError, match="payload"):
        run_log.append_event(run.id, EventKind.LOG, payload)  # type: ignore[arg-type]
    assert len(run_log.events_since(0)) == 1


def test_untrusted_text_is_stored_as_data(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    text = "'); DROP TABLE runs; --"
    run_log.append_event(run.id, EventKind.AGENT_MESSAGE, {"text": text})
    run_log.set_run_status(run.id, RunStatus.BLOCKED, text)
    assert run_log.get_run(run.id).reason == text
    assert run_log.events_since(0)[1].payload == {"text": text}


# Publishing ---------------------------------------------------------------------------


def test_committed_events_are_published_in_order(workspace: Path, clock: FixedClock) -> None:
    bus = EventBus()
    with (
        RunLog(workspace, bus=bus, clock=clock, daemon_instance="A") as log,
        bus.subscribe() as sub,
    ):
        run = log.start_run("T04")
        attempt = log.start_attempt(run.id, AttemptKind.INITIAL)
        log.finish_attempt(attempt.id, AttemptStatus.APPROVED)
        log.set_run_status(run.id, RunStatus.DONE)
        received = [sub.get(timeout=1) for _ in range(4)]
        assert received == log.events_since(0)


def test_failed_insert_publishes_nothing(workspace: Path, clock: FixedClock) -> None:
    bus = EventBus()
    with (
        RunLog(workspace, bus=bus, clock=clock, daemon_instance="A") as log,
        bus.subscribe() as sub,
    ):
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            log.append_event(99, EventKind.LOG, {"msg": "orphan"})
        assert sub.get(timeout=0) is None
        assert log.events_since(0) == []


def test_concurrent_appends_get_increasing_ids(workspace: Path, clock: FixedClock) -> None:
    bus = EventBus()
    with RunLog(workspace, bus=bus, clock=clock, daemon_instance="A") as log:
        run = log.start_run("T04")
        start = log.events_since(0)[-1].id
        with bus.subscribe(maxsize=2000) as sub:
            errors: list[BaseException] = []

            def work(worker: int) -> None:
                try:
                    for i in range(250):
                        log.append_event(run.id, EventKind.LOG, {"worker": worker, "i": i})
                except BaseException as exc:  # reported below
                    errors.append(exc)

            threads = [threading.Thread(target=work, args=(n,)) for n in range(4)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            assert errors == []

            stored = log.events_since(start, limit=2000)
            ids = [e.id for e in stored]
            assert len(ids) == 1000
            assert all(a < b for a, b in zip(ids, ids[1:], strict=False))

            received = []
            while (event := sub.get(timeout=0)) is not None:
                received.append(event.id)
            assert received == ids
            assert not sub.lagged


def test_paused_run_keeps_reset_at_until_the_next_change(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    reset = datetime(2026, 10, 18, 14, 0, tzinfo=UTC)

    paused = run_log.set_run_status(run.id, RunStatus.PAUSED, "usage limit", reset_at=reset)
    assert paused.reset_at == "2026-10-18T14:00:00.000Z"
    assert run_log.events_since(0)[-1].payload["reset_at"] == "2026-10-18T14:00:00.000Z"
    assert run_log.set_run_status(run.id, RunStatus.RUNNING).reset_at is None


def test_reopen_run_only_from_interrupted(workspace: Path) -> None:
    with RunLog(workspace, daemon_instance="old") as old:
        run = old.start_run("T04")
    with RunLog(workspace, daemon_instance="new") as log:
        with pytest.raises(ValueError, match="run 1 is running, not interrupted"):
            log.reopen_run(run.id)
        recover_interrupted(log)

        reopened = log.reopen_run(run.id)

        assert reopened.status is RunStatus.RUNNING
        assert reopened.ended_at is None and reopened.reason is None
        assert reopened.daemon_instance == "new"
        assert log.events_since(0)[-1].payload == {
            "from": "interrupted",
            "to": "running",
            "reason": "resumed",
        }


def test_progress_note_is_stored_on_the_run(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    assert run.progress_note is None
    assert run_log.set_progress_note(run.id, "Added X.").progress_note == "Added X."
    assert run_log.get_run(run.id).progress_note == "Added X."


def test_version_1_database_is_migrated(workspace: Path) -> None:
    path = state_db_path(workspace)
    path.parent.mkdir()
    conn = sqlite3.connect(path)
    for statement in db._statements(db.MIGRATIONS[0]):
        conn.execute(statement)
    conn.execute(
        "INSERT INTO runs (ticket_id, status, daemon_instance, started_at) "
        "VALUES ('T04', 'done', 'A', '2026-10-18T09:00:00.000Z')"
    )
    conn.execute("PRAGMA user_version = 1")
    conn.commit()
    conn.close()

    with RunLog(workspace, daemon_instance="A") as log:
        run = log.get_run(1)
        usage = log.run_usage(1)
    assert (run.status, run.progress_note, run.reset_at) == (RunStatus.DONE, None, None)
    assert usage.cache_read_tokens == 0
