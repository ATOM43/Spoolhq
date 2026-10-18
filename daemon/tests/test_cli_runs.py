"""`spool runs list|show`: read-only views of a project's run log."""

from pathlib import Path

from conftest import FixedClock
from typer.testing import CliRunner

from spoolhq.cli import app
from spoolhq.services.runs import AttemptKind, AttemptStatus, RunLog, RunStatus, state_db_path

runner = CliRunner()


def seed(workspace: Path, clock: FixedClock) -> tuple[int, int]:
    """Run 1 (T04): two attempts, done. Run 2 (T05): one attempt, still running."""
    with RunLog(workspace, clock=clock, daemon_instance="old") as log:
        first = log.start_run("T04")
        a1 = log.start_attempt(first.id, AttemptKind.INITIAL, backend="claude", model="m1")
        log.record_usage(a1.id, 100, 50, 1500)
        log.finish_attempt(a1.id, AttemptStatus.GATES_FAILED)
        a2 = log.start_attempt(first.id, AttemptKind.GATE_RETRY)
        log.record_usage(a2.id, 10, 5)
        log.finish_attempt(a2.id, AttemptStatus.APPROVED)
        log.set_run_status(first.id, RunStatus.DONE)
        second = log.start_run("T05")
        log.start_attempt(second.id, AttemptKind.INITIAL)
        return first.id, second.id


def test_runs_list_shows_newest_first(workspace: Path, clock: FixedClock) -> None:
    first, second = seed(workspace, clock)

    result = runner.invoke(app, ["runs", "list", "demo"])

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0].split() == ["ID", "TICKET", "STATUS", "STARTED", "ATTEMPTS", "TOKENS"]
    assert lines[1].split() == [str(second), "T05", "running", lines[1].split()[3], "1", "0"]
    assert lines[2].split() == [str(first), "T04", "done", "2026-10-18T09:00:00.000Z", "2", "165"]


def test_runs_list_filters_by_ticket(workspace: Path, clock: FixedClock) -> None:
    seed(workspace, clock)
    result = runner.invoke(app, ["runs", "list", "demo", "--ticket", "T04"])
    assert result.exit_code == 0, result.output
    assert "T04" in result.output
    assert "T05" not in result.output

    result = runner.invoke(app, ["runs", "list", "demo", "--ticket", "T99"])
    assert result.exit_code == 0
    assert result.output.strip() == "No runs of T99 yet."

    result = runner.invoke(app, ["runs", "list", "demo", "--ticket", "../x"])
    assert result.exit_code == 1
    assert "invalid ticket id" in result.output


def test_runs_show_lists_attempts_with_folders(workspace: Path, clock: FixedClock) -> None:
    first, _ = seed(workspace, clock)

    result = runner.invoke(app, ["runs", "show", "demo", str(first)])

    assert result.exit_code == 0, result.output
    out = result.output
    assert f"id:         {first}" in out
    assert "ticket:     T04" in out
    assert "status:     done" in out
    assert "tokens:     110 in · 55 out" in out
    assert "cost:       $0.001500" in out
    assert "Attempts (2):" in out
    attempt_lines = [line.split() for line in out.splitlines() if "runs/T04/" in line]
    assert attempt_lines == [
        ["1", "initial", "gates_failed", "100", "50", "$0.001500", "runs/T04/001"],
        ["2", "gate_retry", "approved", "10", "5", "-", "runs/T04/002"],
    ]


def test_runs_show_a_run_without_attempts(workspace: Path, clock: FixedClock) -> None:
    with RunLog(workspace, clock=clock, daemon_instance="x") as log:
        run = log.start_run("T04")
    result = runner.invoke(app, ["runs", "show", "demo", str(run.id)])
    assert result.exit_code == 0, result.output
    assert "Attempts: none" in result.output
    assert "cost:       -" in result.output


def test_unknown_run_exits_1(workspace: Path, clock: FixedClock) -> None:
    result = runner.invoke(app, ["runs", "show", "demo", "99"])
    assert result.exit_code == 1
    assert result.output.strip() == "error: run 99 not found"

    seed(workspace, clock)
    result = runner.invoke(app, ["runs", "show", "demo", "99"])
    assert result.exit_code == 1
    assert result.output.strip() == "error: run 99 not found"


def test_unknown_project_exits_1(projects_dir: Path) -> None:
    for command in (["runs", "list", "nope"], ["runs", "show", "nope", "1"]):
        result = runner.invoke(app, command)
        assert result.exit_code == 1
        assert result.output.strip() == f"error: no project 'nope' in {projects_dir}"
    result = runner.invoke(app, ["runs", "list", "../etc"])
    assert result.exit_code == 1
    assert "invalid project name" in result.output


def test_project_without_runs(workspace: Path) -> None:
    result = runner.invoke(app, ["runs", "list", "demo"])
    assert result.exit_code == 0
    assert result.output.strip() == "No runs in 'demo' yet."
    assert not state_db_path(workspace).exists()


def test_corrupt_database_exits_1(workspace: Path) -> None:
    path = state_db_path(workspace)
    path.parent.mkdir()
    path.write_text("not a database\n" * 50, encoding="utf-8")
    result = runner.invoke(app, ["runs", "list", "demo"])
    assert result.exit_code == 1
    assert result.output.strip() == (
        "error: state.db: not a SpoolHQ database (file is not a database)"
    )


def test_reading_never_recovers_a_stale_run(workspace: Path, clock: FixedClock) -> None:
    _, stale = seed(workspace, clock)
    before = state_db_path(workspace).read_bytes()

    for command in (["runs", "list", "demo"], ["runs", "show", "demo", str(stale)]):
        result = runner.invoke(app, command)
        assert result.exit_code == 0, result.output
        assert "running" in result.output

    with RunLog.open_read_only(workspace) as reader:
        run = reader.get_run(stale)
        assert run.status is RunStatus.RUNNING
        assert run.ended_at is None
        assert len(reader.events_since(0)) == 8
    assert state_db_path(workspace).read_bytes() == before
