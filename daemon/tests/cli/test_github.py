"""`spool secrets set github`, `spool github sync`, and PR lines in `run status` and
`tickets show`."""

import getpass
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from spoolhq.cli import github as github_cli
from spoolhq.cli import run as run_cli
from spoolhq.cli.client import ApiClient
from spoolhq.cli.main import app
from spoolhq.services.runs import RunLog, RunStatus, set_pull_request
from tests.conftest import MemoryKeyring

runner = CliRunner()
URL = "https://github.com/acme/demo/pull/3"


def test_secrets_set_github_reads_a_hidden_prompt(
    keychain: MemoryKeyring, monkeypatch: pytest.MonkeyPatch
) -> None:
    prompts: list[str] = []

    def fake_getpass(prompt: str) -> str:
        prompts.append(prompt)
        return "ghp_from_prompt\n"

    monkeypatch.setattr(getpass, "getpass", fake_getpass)
    result = runner.invoke(app, ["secrets", "set", "github"])
    assert result.exit_code == 0, result.output
    assert prompts == ["GitHub token (input hidden): "]
    assert keychain.passwords == {("spoolhq", "github"): "ghp_from_prompt"}
    assert "ghp_from_prompt" not in result.output
    assert "Stored the GitHub token in the OS keychain" in result.output


def test_secrets_set_refuses_other_names_and_empty_tokens(
    keychain: MemoryKeyring, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert runner.invoke(app, ["secrets", "set", "clickup"]).exit_code == 1
    monkeypatch.setattr(getpass, "getpass", lambda prompt: "  ")
    result = runner.invoke(app, ["secrets", "set", "github"])
    assert result.exit_code == 1
    assert "error: the token is empty" in result.output
    assert keychain.passwords == {}


def test_secrets_set_without_a_keychain(monkeypatch: pytest.MonkeyPatch) -> None:
    from keyring.errors import NoKeyringError

    def no_keyring(token: str) -> None:
        raise NoKeyringError("none")

    monkeypatch.setattr(getpass, "getpass", lambda prompt: "t")
    monkeypatch.setattr(github_cli, "store_github_token", no_keyring)
    result = runner.invoke(app, ["secrets", "set", "github"])
    assert result.exit_code == 1
    assert "cannot write to the OS keychain (NoKeyringError)" in result.output
    assert "set SPOOLHQ_GITHUB_TOKEN" in result.output


def daemon_answering(monkeypatch: pytest.MonkeyPatch, status: int, body: object) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(status, json=body))
    client = ApiClient("http://127.0.0.1:8765", "t", transport=transport)
    monkeypatch.setattr(github_cli, "_client", lambda: client)


def test_github_sync_prints_each_line(monkeypatch: pytest.MonkeyPatch) -> None:
    daemon_answering(monkeypatch, 200, {"lines": ["T01: PR #3 open", "T02: blocked"]})
    result = runner.invoke(app, ["github", "sync", "demo"])
    assert (result.exit_code, result.output) == (0, "T01: PR #3 open\nT02: blocked\n")

    daemon_answering(monkeypatch, 200, {"lines": []})
    assert runner.invoke(app, ["github", "sync", "demo"]).output == (
        "no open pull requests in 'demo'\n"
    )

    daemon_answering(monkeypatch, 409, {"detail": "'demo' has no git.remote"})
    result = runner.invoke(app, ["github", "sync", "demo"])
    assert (result.exit_code, result.output) == (1, "error: 'demo' has no git.remote\n")


def test_github_sync_through_the_api(run_client: TestClient, token: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    assert run_client.post("/api/projects/demo/github/sync").status_code == 401
    response = run_client.post("/api/projects/demo/github/sync", headers=headers)
    assert response.status_code == 409
    assert response.json() == {"detail": "'demo' has no git.remote"}
    missing = run_client.post("/api/projects/nope/github/sync", headers=headers)
    assert missing.status_code == 404


def test_run_status_shows_the_pull_request(monkeypatch: pytest.MonkeyPatch) -> None:
    run = {
        "id": 3,
        "ticket_id": "T04",
        "status": "awaiting_approval",
        "pr_number": 3,
        "pr_url": URL,
    }
    waiting = {"active": False, "run": run, "last_merged": None}
    monkeypatch.setattr(run_cli, "_call", lambda method, path, body=None: waiting)
    assert runner.invoke(app, ["run", "status", "demo"]).output == (
        f"no active run in 'demo'\nT04 · awaiting_approval · PR #3 · {URL}\n"
    )

    active = {
        "active": True,
        "run": {**run, "status": "running"},
        "attempts": 2,
        "input_tokens": 1,
        "output_tokens": 1,
        "phases": [],
    }
    monkeypatch.setattr(run_cli, "_call", lambda method, path, body=None: active)
    assert runner.invoke(app, ["run", "status", "demo"]).output == (
        f"run 3 · T04 · running · 2 attempts · 2 tokens\nPR #3 · {URL}\n"
    )


def test_tickets_show_the_pull_request(run_project: Path) -> None:
    with RunLog(run_project, daemon_instance="A") as log:
        run = log.start_run("T07")
        log.set_run_status(run.id, RunStatus.AWAITING_APPROVAL)
        set_pull_request(log, run.id, 3, URL, "spoolhq/T07-x")
    result = runner.invoke(app, ["tickets", "show", "demo", "T07"])
    assert result.exit_code == 0, result.output
    assert f"pull_request:    #3 {URL} (awaiting_approval)\n" in result.output
