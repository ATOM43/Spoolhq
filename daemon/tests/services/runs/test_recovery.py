"""Crash recovery: runs a stopped daemon left active become interrupted."""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from spoolhq.cli import app
from spoolhq.services.runs import (
    INTERRUPTED_REASON,
    AttemptKind,
    AttemptStatus,
    EventKind,
    RunLog,
    RunStatus,
    recover_interrupted,
)
from tests.conftest import FixedClock

runner = CliRunner()

CRASHING_DAEMON = textwrap.dedent(
    """
    import sys, time
    from pathlib import Path
    from spoolhq.services.runs import AttemptKind, EventKind, RunLog

    log = RunLog(Path(sys.argv[1]), daemon_instance="A")
    run = log.start_run("T04")
    attempt = log.start_attempt(run.id, AttemptKind.INITIAL)
    for i in range(3):
        log.append_event(run.id, EventKind.AGENT_MESSAGE, {"i": i}, attempt_id=attempt.id)
    print("ready", flush=True)
    time.sleep(600)
    """
)


@pytest.mark.integration
def test_killed_daemon_leaves_an_interrupted_run(workspace: Path) -> None:
    process = subprocess.Popen(  # noqa: S603 - fixed argument list, no shell
        [sys.executable, "-c", CRASHING_DAEMON, str(workspace)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout is not None
        line = process.stdout.readline()
        assert line.strip() == "ready", process.stderr.read() if process.stderr else ""
    finally:
        process.kill()
        process.communicate(timeout=30)

    with RunLog(workspace, daemon_instance="B") as log:
        recovered = recover_interrupted(log)
        assert [run.ticket_id for run in recovered] == ["T04"]
        run = log.get_run(recovered[0].id)
        assert run.status is RunStatus.INTERRUPTED
        assert run.reason == INTERRUPTED_REASON
        assert run.ended_at is not None
        assert run.daemon_instance == "A"
        (attempt,) = log.list_attempts(run.id)
        assert attempt.status is AttemptStatus.INTERRUPTED
        assert attempt.ended_at is not None

        events = log.events_since(0)
        kinds = [e.kind for e in events]
        assert kinds.count(EventKind.RUN_INTERRUPTED) == 1
        assert [e.payload["i"] for e in events if e.kind is EventKind.AGENT_MESSAGE] == [0, 1, 2]
        assert events[-1].kind is EventKind.RUN_INTERRUPTED
        assert events[-1].payload["attempt_ids"] == [attempt.id]

        assert recover_interrupted(log) == []
        assert log.events_since(0) == events

    result = runner.invoke(app, ["runs", "list", "demo"])
    assert result.exit_code == 0, result.output
    assert "interrupted" in result.output
    assert "running" not in result.output


def test_recovery_scope(workspace: Path, clock: FixedClock) -> None:
    with RunLog(workspace, clock=clock, daemon_instance="old") as old:
        paused = old.start_run("T01")
        old.start_attempt(paused.id, AttemptKind.INITIAL)
        old.set_run_status(paused.id, RunStatus.PAUSED, "usage limit")
        waiting = old.start_run("T02")
        finished = old.start_attempt(waiting.id, AttemptKind.INITIAL)
        old.finish_attempt(finished.id, AttemptStatus.APPROVED)
        old.set_run_status(waiting.id, RunStatus.AWAITING_APPROVAL)
        done = old.start_run("T03")
        old.set_run_status(done.id, RunStatus.DONE)
        blocked = old.start_run("T05")
        old.set_run_status(blocked.id, RunStatus.BLOCKED)
        cancelled = old.start_run("T06")
        old.set_run_status(cancelled.id, RunStatus.CANCELLED)
        done_attempt_run = old.start_run("T07")
        stale_attempt = old.start_attempt(done_attempt_run.id, AttemptKind.INITIAL)
        old.finish_attempt(stale_attempt.id, AttemptStatus.GATES_FAILED)
        second = old.start_attempt(done_attempt_run.id, AttemptKind.GATE_RETRY)

    with RunLog(workspace, clock=clock, daemon_instance="current") as log:
        mine = log.start_run("T04")
        before = {run.id: run for run in log.list_runs()}
        events_before = len(log.events_since(0))

        recovered = recover_interrupted(log)

        assert [run.id for run in recovered] == [paused.id, done_attempt_run.id]
        after = {run.id: run for run in log.list_runs()}
        assert after[paused.id].status is RunStatus.INTERRUPTED
        assert after[paused.id].reason == INTERRUPTED_REASON
        for run_id in (waiting.id, done.id, blocked.id, cancelled.id, mine.id):
            assert after[run_id] == before[run_id]
        assert after[mine.id].status is RunStatus.RUNNING

        statuses = {a.number: a.status for a in log.list_attempts(done_attempt_run.id)}
        assert statuses == {1: AttemptStatus.GATES_FAILED, 2: AttemptStatus.INTERRUPTED}
        assert log.get_attempt(second.id).ended_at is not None
        assert [a.status for a in log.list_attempts(waiting.id)] == [AttemptStatus.APPROVED]

        new_events = log.events_since(0)[events_before:]
        assert [(e.kind, e.run_id) for e in new_events] == [
            (EventKind.RUN_INTERRUPTED, paused.id),
            (EventKind.RUN_INTERRUPTED, done_attempt_run.id),
        ]
        assert new_events[0].payload["from"] == "paused"
        assert recover_interrupted(log) == []
        assert len(log.events_since(0)) == events_before + 2
