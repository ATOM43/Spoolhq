"""`spool run`: the commands call the daemon's run endpoints and follow the run."""

import httpx
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from spoolhq.cli import run as run_cli
from spoolhq.cli.client import ApiClient
from spoolhq.cli.main import app
from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import Agents
from tests.conftest import REVIEW_FIXTURES

runner = CliRunner()


@pytest.fixture
def daemon(run_client: TestClient, token: str, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Point `spool run` at the in-process app (with fake agents), polling fast."""

    def forward(request: httpx.Request) -> httpx.Response:
        return run_client.request(
            request.method, request.url.path, content=request.content, headers=request.headers
        )

    monkeypatch.setattr(
        run_cli,
        "_client",
        lambda: ApiClient("http://127.0.0.1:8765", token, transport=httpx.MockTransport(forward)),
    )
    monkeypatch.setattr(run_cli, "POLL_S", 0.02)
    return run_client


def test_status_with_no_run(daemon: TestClient) -> None:
    result = runner.invoke(app, ["run", "status", "demo"])
    assert result.exit_code == 0
    assert result.output == "no active run in 'demo'\n"


@pytest.mark.integration
def test_next_follows_the_run_to_its_end(daemon: TestClient) -> None:
    result = runner.invoke(app, ["run", "next", "demo"])

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0] == "T07 · Parse slugs · run 1"
    assert "T07 attempt 1 · implement (initial)" in lines
    assert any(line.startswith("T07 attempt 1 · commit · ") for line in lines)
    assert "T07 attempt 1 · gates · ✓ passed" in lines
    assert "T07 attempt 1 · review · approve" in lines
    assert lines[-1].startswith("T07 approved; merging arrives in T14 — worktree kept at ")
    assert runner.invoke(app, ["run", "status", "demo"]).output == "no active run in 'demo'\n"


def test_status_of_an_active_run(monkeypatch: pytest.MonkeyPatch) -> None:
    current = {
        "active": True,
        "run": {"id": 12, "ticket_id": "T04", "status": "paused"},
        "attempts": 2,
        "input_tokens": 1000,
        "output_tokens": 234,
        "phases": [{"id": 9, "text": "T04 · paused · the implementer hit a usage limit"}],
    }
    monkeypatch.setattr(run_cli, "_call", lambda method, path, body=None: current)

    result = runner.invoke(app, ["run", "status", "demo"])

    assert result.output == (
        "run 12 · T04 · paused · 2 attempts · 1,234 tokens\n"
        "T04 · paused · the implementer hit a usage limit\n"
    )


def test_errors_from_the_daemon_exit_1(daemon: TestClient) -> None:
    result = runner.invoke(app, ["run", "next", "demo", "T99"])
    assert result.exit_code == 1
    assert "error: ticket T99 not found in 'demo'" in result.output

    result = runner.invoke(app, ["run", "pause", "demo"])
    assert result.exit_code == 1
    assert "error: no run in 'demo'" in result.output

    result = runner.invoke(app, ["run", "discard", "demo", "T07"])
    assert result.exit_code == 1
    assert "error: T07 is ready" in result.output


def test_ctrl_c_detaches(daemon: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def interrupt(_seconds: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(run_cli.time, "sleep", interrupt)
    monkeypatch.setattr(
        run_cli,
        "_call",
        lambda method, path, body=None: {"phases": [], "working": True, "run": None},
    )

    result = runner.invoke(app, ["run", "all", "demo"])

    assert result.exit_code == 0
    assert result.output == "run continues in the daemon; spool run status to check\n"


@pytest.mark.integration
def test_cancel_resume_discard_and_status(
    daemon: TestClient, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A run that blocks: the reviewer asks for a person.
    loop = daemon.app.state.runloop  # type: ignore[attr-defined]
    reviewer = FakeRunner(REVIEW_FIXTURES / "needs_human.jsonl")
    monkeypatch.setattr(loop, "agents", Agents(loop.agents.implementer, reviewer))
    result = runner.invoke(app, ["run", "next", "demo"])
    assert result.exit_code == 1
    assert result.output.splitlines()[-1].startswith("T07 · blocked · the reviewer asked")

    result = runner.invoke(app, ["run", "discard", "demo", "T07"])
    assert (result.exit_code, result.output) == (0, "T07 discarded; it is ready again\n")
    result = runner.invoke(app, ["run", "cancel", "demo"])
    assert result.exit_code == 1
    assert "error: no active run in 'demo'" in result.output
    result = runner.invoke(app, ["run", "resume", "demo", "--run", "1"])
    assert "error: nothing to resume in 'demo'" in result.output
