"""``POST /api/shutdown``: cancels the active run like Cancel does, then asks to exit."""

import time
from pathlib import Path

from fastapi.testclient import TestClient

from spoolhq.api import create_app
from spoolhq.core.config import load_settings
from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import Agents
from spoolhq.services.runs import RunLog
from spoolhq.services.tickets import load_ticket
from tests.conftest import AGENT_FIXTURES, REVIEW_FIXTURES


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def slow_client(token: str) -> TestClient:
    """The implementer waits 0.5 s between messages, so the run is still going."""
    app = create_app(
        load_settings(),
        token=token,
        agents=Agents(
            implementer=FakeRunner(AGENT_FIXTURES / "success_writes_file.jsonl", delay_s=0.5),
            reviewer=FakeRunner(REVIEW_FIXTURES / "approve.jsonl"),
        ),
    )
    exits: list[str] = []
    app.state.request_exit = lambda: exits.append("exit")
    client = TestClient(app, base_url=f"http://127.0.0.1:{load_settings().port}")
    client.exits = exits  # type: ignore[attr-defined]
    return client


def test_shutdown_cancels_the_run_removes_its_worktree_and_exits(
    run_project: Path, token: str, projects_dir: Path
) -> None:
    worktree = load_settings().worktrees_dir / "demo" / "T07"
    with slow_client(token) as client:
        started = client.post("/api/projects/demo/run/next", headers=auth(token))
        assert started.status_code == 201, started.text
        for _ in range(100):
            if worktree.is_dir():
                break
            time.sleep(0.05)
        assert worktree.is_dir()

        response = client.post("/api/shutdown", headers=auth(token))

        assert response.status_code == 200
        [run] = response.json()["cancelled"]
        assert (run["ticket_id"], run["status"]) == ("T07", "cancelled")
        assert client.exits == ["exit"]  # type: ignore[attr-defined]
    assert not worktree.exists()
    assert load_ticket("demo", "T07", projects_dir=projects_dir).meta.status == "ready"
    log = RunLog.open_read_only(run_project)
    try:
        assert log.get_run(run["id"]).status.value == "cancelled"  # not interrupted
    finally:
        log.close()


def test_shutdown_when_idle_just_exits(run_project: Path, token: str) -> None:
    with slow_client(token) as client:
        response = client.post("/api/shutdown", headers=auth(token))
        assert response.status_code == 200
        assert response.json() == {"cancelled": []}
        assert client.exits == ["exit"]  # type: ignore[attr-defined]


def test_shutdown_needs_the_token(run_project: Path, token: str) -> None:
    with slow_client(token) as client:
        assert client.post("/api/shutdown").status_code == 401
        assert client.post("/api/shutdown", headers=auth("wrong")).status_code == 401
        assert client.exits == []  # type: ignore[attr-defined]
