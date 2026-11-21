"""`spool tracker status|push [--dry-run]`."""

from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from spoolhq.cli import tracker as tracker_cli
from spoolhq.cli.client import ApiClient
from spoolhq.cli.main import app
from spoolhq.services.runs import RunLog, RunRegistry, outbox, set_pull_request
from spoolhq.services.tracker.sync import TrackerSync
from tests.services.tracker.fakes import TOKEN, FakeClickUp
from tests.services.tracker.test_sync import finished_run, set_tracker, write_ticket

runner = CliRunner()


def daemon_answering(monkeypatch: pytest.MonkeyPatch, status: int, body: object) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(status, json=body))
    client = ApiClient("http://127.0.0.1:8765", "t", transport=transport)
    monkeypatch.setattr(tracker_cli, "_client", lambda: client)


def test_status_lines(monkeypatch: pytest.MonkeyPatch) -> None:
    view = {
        "kind": "clickup",
        "state": "failed",
        "pending": 2,
        "last_error": "ClickUp answered 500",
        "last_synced_at": None,
    }
    daemon_answering(monkeypatch, 200, view)
    result = runner.invoke(app, ["tracker", "status", "demo"])
    assert result.output == (
        "demo: clickup · failed · 2 pending\nlast synced: never\nlast error: ClickUp answered 500\n"
    )

    daemon_answering(monkeypatch, 200, {**view, "state": "off", "kind": None})
    assert "no tracker" in runner.invoke(app, ["tracker", "status", "demo"]).output

    daemon_answering(monkeypatch, 404, {"error": {"code": "not_found", "message": "no project"}})
    result = runner.invoke(app, ["tracker", "status", "demo"])
    assert (result.exit_code, result.output) == (1, "error: no project\n")


def test_push_asks_the_daemon(monkeypatch: pytest.MonkeyPatch) -> None:
    daemon_answering(monkeypatch, 200, {"queued": 3})
    result = runner.invoke(app, ["tracker", "push", "demo"])
    assert result.output == "queued 3 action(s); see `spool tracker status demo`\n"
    daemon_answering(monkeypatch, 409, {"error": {"code": "conflict", "message": "no tracker"}})
    assert runner.invoke(app, ["tracker", "push", "demo"]).exit_code == 1


def snapshot(root: Path) -> dict[str, bytes]:
    """Every file's bytes; SQLite's WAL side files appear on any read, so they're left out."""
    return {
        str(p): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.name.endswith(("-shm", "-wal"))
    }


def test_dry_run_prints_every_action_and_changes_nothing(
    workspace: Path, projects_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SPOOLHQ_CLICKUP_TOKEN", TOKEN)
    set_tracker(projects_dir)
    write_ticket(workspace, "T01")
    write_ticket(workspace, "T02", status="draft")
    server = FakeClickUp()
    registry = RunRegistry.start(projects_dir, daemon_instance="A")
    try:
        sync = TrackerSync(registry, projects_dir=projects_dir, transport=server.transport)
        sync.tick("demo")  # T01 and T02 synced; the baseline is set
        run_log = registry.get("demo").run_log
        run_id = finished_run(run_log)
        set_pull_request(run_log, run_id, 4, "https://github.com/o/r/pull/4", "b")
    finally:
        registry.close()
    write_ticket(workspace, "T03")
    before, requests = snapshot(workspace), len(server.requests)
    sent: list[httpx.Request] = []
    original: Callable[..., httpx.Response] = httpx.Client.send

    def record(self: httpx.Client, request: httpx.Request, **kwargs: object) -> httpx.Response:
        sent.append(request)
        return original(self, request, **kwargs)

    monkeypatch.setattr(httpx.Client, "send", record)

    result = runner.invoke(app, ["tracker", "push", "demo", "--dry-run"])

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "update t1: T01 · Thing T01 (status: to do)",
        "update t2: T02 · Thing T02 (status: to do)",
        "create: T03 · Thing T03 (status: to do)",
        f"comment: T01 · run {run_id} done",
        "comment: T01 · Pull request: https://github.com/o/r/pull/4",
        "dry run: 5 action(s), nothing sent",
    ]
    assert snapshot(workspace) == before
    assert sent == [] and len(server.requests) == requests
    with RunLog.open_read_only(workspace) as reader:
        assert outbox.sync_state(reader).pending == 0


def test_dry_run_without_runs_or_a_tracker(workspace: Path, projects_dir: Path) -> None:
    result = runner.invoke(app, ["tracker", "push", "demo", "--dry-run"])
    assert (result.exit_code, result.output) == (
        1,
        "error: 'demo' has no tracker block in project.yaml\n",
    )
    set_tracker(projects_dir)
    write_ticket(workspace, "T01")
    result = runner.invoke(app, ["tracker", "push", "demo", "--dry-run"])
    assert result.output.splitlines()[0] == "create: T01 · Thing T01 (status: to do)"
    assert not (workspace / ".spoolhq" / "state.db").exists()
