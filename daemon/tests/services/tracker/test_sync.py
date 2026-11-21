"""The tracker sync: the outbox, idempotent pushes, retries, rate limits, run comments.

Every test runs against the fake ClickUp API; time is a manual clock, so no test sleeps.
"""

import logging
import time
from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path

import pytest

from spoolhq.services.projects import load_project, save_project
from spoolhq.services.projects.model import Tracker
from spoolhq.services.runs import (
    AttemptKind,
    AttemptStatus,
    EventKind,
    RunLog,
    RunRegistry,
    RunStatus,
    set_pull_request,
)
from spoolhq.services.scheduler import apply_transition
from spoolhq.services.tickets import load_ticket
from spoolhq.services.tracker.sync import TrackerSync, retry_delay
from tests.conftest import CLOCK_START
from tests.services.tracker.fakes import TOKEN, FakeClickUp

SCOPE = "Make the thing work end to end."


class ManualClock:
    def __init__(self) -> None:
        self.now = CLOCK_START

    def __call__(self):  # type: ignore[no-untyped-def]
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def write_ticket(workspace: Path, ticket_id: str, status: str = "ready") -> None:
    (workspace / "tickets").mkdir(exist_ok=True)
    (workspace / "tickets" / f"{ticket_id}-thing.md").write_text(
        f"---\nid: {ticket_id}\ntitle: Thing {ticket_id}\nphase: 1\nstatus: {status}\n"
        f"estimate_h: 1\n---\n\n## Scope\n{SCOPE}\n\n## Done when\n- [ ] it works\n",
        encoding="utf-8",
    )


def set_tracker(projects_dir: Path, **fields: object) -> None:
    project = load_project("demo", projects_dir=projects_dir)
    project.tracker = Tracker(kind="clickup", list_id="123", **fields)  # type: ignore[arg-type]
    save_project(project, projects_dir=projects_dir)


@pytest.fixture
def server() -> FakeClickUp:
    return FakeClickUp()


@pytest.fixture
def clock() -> ManualClock:  # type: ignore[override]
    return ManualClock()


@pytest.fixture
def demo(workspace: Path, projects_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("SPOOLHQ_CLICKUP_TOKEN", TOKEN)
    set_tracker(projects_dir)
    write_ticket(workspace, "T01")
    write_ticket(workspace, "T02")
    return workspace


@pytest.fixture
def registry(demo: Path, projects_dir: Path) -> Iterator[RunRegistry]:
    found = RunRegistry.start(projects_dir, daemon_instance="A")
    yield found
    found.close()


def make_sync(
    registry: RunRegistry, projects_dir: Path, server: FakeClickUp, clock: ManualClock
) -> TrackerSync:
    return TrackerSync(registry, projects_dir=projects_dir, transport=server.transport, clock=clock)


@pytest.fixture
def sync(
    registry: RunRegistry, projects_dir: Path, server: FakeClickUp, clock: ManualClock
) -> Iterator[TrackerSync]:
    found = make_sync(registry, projects_dir, server, clock)
    yield found
    found.close()


def refs(projects_dir: Path) -> dict[str, str | None]:
    return {
        tid: load_ticket("demo", tid, projects_dir=projects_dir).meta.tracker_ref
        for tid in ("T01", "T02")
    }


def finished_run(run_log: RunLog, ticket_id: str = "T01") -> int:
    run = run_log.start_run(ticket_id)
    attempt = run_log.start_attempt(run.id, AttemptKind.INITIAL, "claude-code-cli")
    run_log.record_usage(attempt.id, 1200, 300, cost_micro_usd=420_000)
    run_log.finish_attempt(attempt.id, AttemptStatus.APPROVED)
    run_log.set_run_status(run.id, RunStatus.DONE)
    return run.id


def test_pushing_twice_creates_no_duplicate_tasks(
    sync: TrackerSync, server: FakeClickUp, projects_dir: Path
) -> None:
    assert sync.tick("demo") == 2
    first = refs(projects_dir)
    assert sorted(t.name for t in server.tasks.values()) == ["T01 · Thing T01", "T02 · Thing T02"]
    assert set(first.values()) == set(server.tasks)

    assert sync.push_all("demo") == 2
    server.requests.clear()
    assert sync.tick("demo") == 2

    assert len(server.tasks) == 2
    assert refs(projects_dir) == first
    assert [r.method for r in server.writes()] == ["PUT", "PUT"]
    assert sync.status("demo").state == "ok"


def test_nothing_changed_queues_nothing(sync: TrackerSync, server: FakeClickUp) -> None:
    sync.tick("demo")
    server.requests.clear()
    assert sync.tick("demo") == 0
    assert server.requests == []


def test_a_crash_before_the_ref_is_written_adopts_the_task(
    registry: RunRegistry,
    projects_dir: Path,
    server: FakeClickUp,
    clock: ManualClock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    crashing = make_sync(registry, projects_dir, server, clock)

    def crash(*args: object) -> None:
        raise SystemExit("daemon killed")

    monkeypatch.setattr(crashing, "_write_ref", crash)
    with pytest.raises(SystemExit):
        crashing.tick("demo")
    assert len(server.tasks) == 1 and refs(projects_dir)["T01"] is None
    monkeypatch.undo()
    monkeypatch.setenv("SPOOLHQ_CLICKUP_TOKEN", TOKEN)

    restarted = make_sync(registry, projects_dir, server, clock)
    restarted.push_all("demo")
    restarted.tick("demo")

    assert len(server.tasks) == 2
    assert refs(projects_dir)["T01"] == "t1"


def test_a_status_change_maps_through_the_status_map(
    sync: TrackerSync, server: FakeClickUp, projects_dir: Path
) -> None:
    sync.tick("demo")
    server.requests.clear()
    apply_transition("demo", "T01", "running", projects_dir=projects_dir)

    assert sync.tick("demo") == 1
    [put] = server.writes()
    assert put.method == "PUT" and put.content == b'{"status":"in progress"}'


def test_status_updates_for_one_ticket_coalesce_to_the_latest(
    sync: TrackerSync, server: FakeClickUp, projects_dir: Path
) -> None:
    sync.tick("demo")
    server.requests.clear()
    for status in ("running", "blocked", "running", "done"):
        apply_transition("demo", "T01", status, projects_dir=projects_dir)
        sync.scan("demo", load_project("demo", projects_dir=projects_dir).tracker)  # type: ignore[arg-type]

    assert sync.status("demo").pending == 1
    sync.tick("demo")
    [put] = server.writes()
    assert put.content == b'{"status":"complete"}'


def test_a_status_the_list_lacks_fails_sync_with_the_fixed_message(
    registry: RunRegistry, projects_dir: Path, clock: ManualClock
) -> None:
    server = FakeClickUp(statuses=["to do", "doing", "complete"])
    sync = make_sync(registry, projects_dir, server, clock)
    for failures in range(1, 6):
        sync.tick("demo")
        clock.advance(retry_delay(failures).total_seconds())

    status = sync.status("demo")
    assert status.state == "failed"
    assert status.last_error == (
        "ClickUp list has no status 'in progress'; set tracker.status_map.running"
    )
    assert server.writes() == []


def test_an_outage_fails_sync_and_recovers(
    sync: TrackerSync, server: FakeClickUp, clock: ManualClock, demo: Path, projects_dir: Path
) -> None:
    run_log = sync._run_log("demo")
    sync.tick("demo")  # both tickets synced
    run_id = finished_run(run_log)
    server.fail = 500
    sync.tick("demo")  # the run's comment fails once
    assert sync.status("demo").state == "syncing"
    for failures in range(1, 5):
        server.fail = "timeout" if failures % 2 else 500
        clock.advance(retry_delay(failures).total_seconds())
        sync.tick("demo")
        if failures == 2:
            write_ticket(demo, "T03")  # queued during the outage

    status = sync.status("demo")
    assert status.state == "failed"
    assert status.last_error in ("ClickUp answered 500", "ClickUp timed out")
    failed = [e for e in run_log.events_since(0, run_id) if e.kind is EventKind.TRACKER_FAILED]
    assert [e.payload["action"] for e in failed] == ["comment"]

    server.fail = None
    clock.advance(MAX_WAIT)
    sync.tick("demo")

    status = sync.status("demo")
    assert (status.state, status.pending, status.last_error) == ("ok", 0, None)
    assert "T03 · Thing T03" in {t.name for t in server.tasks.values()}
    assert status.last_synced_at is not None


MAX_WAIT = 600.0


def test_a_rate_limit_waits_as_told_then_succeeds(
    sync: TrackerSync, server: FakeClickUp, clock: ManualClock
) -> None:
    server.rate_limit = str(time.time() + 30)  # the adapter reads the real clock
    assert sync.tick("demo") == 0
    assert sync.status("demo").state == "syncing"
    calls = len(server.requests)

    clock.advance(20)
    assert sync.tick("demo") == 0
    assert len(server.requests) == calls  # still waiting: no call at all

    clock.advance(11)
    assert sync.tick("demo") == 2
    assert sync.status("demo").last_error is None


def test_run_comments_are_built_from_run_data_and_sent_once(
    sync: TrackerSync,
    server: FakeClickUp,
    projects_dir: Path,
    clock: ManualClock,
) -> None:
    run_log = sync._run_log("demo")
    sync.tick("demo")
    run_id = finished_run(run_log)
    set_pull_request(run_log, run_id, 9, "https://github.com/o/r/pull/9", "spoolhq/T01-thing")
    sync.tick("demo")

    [task] = [t for t in server.tasks.values() if t.name.startswith("T01")]
    comment, link = task.comments
    assert comment.splitlines() == [
        f"SpoolHQ run {run_id}: done",
        "Attempts: 1",
        "Usage: 1,500 tokens · $0.42",
        "Pull request: https://github.com/o/r/pull/9",
    ]
    assert SCOPE not in comment
    assert link == "Pull request: https://github.com/o/r/pull/9"

    # A daemon restart: a new registry and sync over the same state.db.
    sync.close()
    sync.registry.close()
    registry = RunRegistry.start(projects_dir, daemon_instance="B")
    try:
        restarted = make_sync(registry, projects_dir, server, clock)
        restarted.tick("demo")
        restarted.push_all("demo")
        restarted.tick("demo")
    finally:
        registry.close()
    assert len(task.comments) == 2


def test_a_commit_shows_when_there_is_no_pull_request(
    sync: TrackerSync, server: FakeClickUp
) -> None:
    run_log = sync._run_log("demo")
    sync.tick("demo")
    run_id = finished_run(run_log)
    run_log.append_event(run_id, EventKind.INTEGRATE, {"commit": "abc1234", "tag": "ticket/T01"})
    sync.tick("demo")
    [task] = [t for t in server.tasks.values() if t.name.startswith("T01")]
    assert task.comments[0].splitlines()[-1] == "Commit: abc1234"


def test_runs_before_sync_started_get_no_comment(
    registry: RunRegistry, projects_dir: Path, server: FakeClickUp, clock: ManualClock
) -> None:
    finished_run(registry.get("demo").run_log)
    make_sync(registry, projects_dir, server, clock).tick("demo")
    assert all(t.comments == [] for t in server.tasks.values())


def test_comment_on_runs_off(sync: TrackerSync, server: FakeClickUp, projects_dir: Path) -> None:
    set_tracker(projects_dir, comment_on_runs=False)
    sync.tick("demo")
    finished_run(sync._run_log("demo"))
    sync.tick("demo")
    assert all(t.comments == [] for t in server.tasks.values())


def test_without_a_tracker_block_nothing_is_queued(
    workspace: Path, projects_dir: Path, server: FakeClickUp, clock: ManualClock
) -> None:
    write_ticket(workspace, "T01")
    registry = RunRegistry.start(projects_dir, daemon_instance="A")
    try:
        sync = make_sync(registry, projects_dir, server, clock)
        sync.start_if_needed()
        assert sync._thread is None
        assert sync.tick("demo") == 0
        assert sync.status("demo").state == "off"
        assert sync.status("demo").pending == 0
    finally:
        registry.close()
    assert server.requests == []


def test_the_thread_starts_with_a_tracker_block(sync: TrackerSync) -> None:
    sync.interval_s = 3600
    sync.start_if_needed()
    assert sync._thread is not None and sync._thread.is_alive()


def test_a_missing_token_is_a_failure(
    sync: TrackerSync, server: FakeClickUp, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SPOOLHQ_CLICKUP_TOKEN")
    for failures in range(1, 6):
        sync.tick("demo")
        sync.clock.advance(retry_delay(failures).total_seconds())  # type: ignore[attr-defined]
    assert sync.status("demo").last_error == (
        "No clickup token; set it in Settings or SPOOLHQ_CLICKUP_TOKEN"
    )
    assert server.requests == []


def test_a_ticket_deleted_locally_is_left_alone(
    sync: TrackerSync, server: FakeClickUp, demo: Path
) -> None:
    sync.scan("demo", load_project("demo", projects_dir=demo.parent).tracker)  # type: ignore[arg-type]
    (demo / "tickets" / "T02-thing.md").unlink()
    sync.tick("demo")
    assert [t.name for t in server.tasks.values()] == ["T01 · Thing T01"]


def test_an_invalid_ticket_file_fails_its_action(
    sync: TrackerSync, server: FakeClickUp, demo: Path
) -> None:
    sync.scan("demo", load_project("demo", projects_dir=demo.parent).tracker)  # type: ignore[arg-type]
    (demo / "tickets" / "T02-thing.md").write_text("---\nid: T02\n---\n", encoding="utf-8")
    sync.tick("demo")
    assert sync.status("demo").pending == 1  # T02's push waits for a retry


def test_the_token_never_leaves_the_request_header(
    sync: TrackerSync,
    server: FakeClickUp,
    clock: ManualClock,
    demo: Path,
    home: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    run_log = sync._run_log("demo")
    sync.tick("demo")
    finished_run(run_log)
    server.fail = 401
    for failures in range(1, 6):
        sync.tick("demo")
        clock.advance(retry_delay(failures).total_seconds())
    server.fail = None
    write_ticket(demo, "T03")
    sync.tick("demo")

    assert TOKEN not in caplog.text
    assert all(TOKEN not in str(e.payload) for e in run_log.events_since(0))
    assert TOKEN not in str(sync.status("demo"))
    for root in (demo, home):
        for path in root.rglob("*"):
            if path.is_file():
                assert TOKEN.encode() not in path.read_bytes(), path
