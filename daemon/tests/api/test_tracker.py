"""The tracker endpoints, and a run that merges while ClickUp hangs."""

import threading
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from spoolhq.api import create_app
from spoolhq.core.config import load_settings
from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import Agents
from tests.api.test_runs import auth, follow
from tests.conftest import AGENT_FIXTURES, REVIEW_FIXTURES, run_git
from tests.services.tracker.fakes import TOKEN, FakeClickUp
from tests.services.tracker.test_sync import set_tracker


@pytest.fixture
def server() -> FakeClickUp:
    return FakeClickUp()


@pytest.fixture
def tracker_client(
    run_project: Path,
    projects_dir: Path,
    token: str,
    server: FakeClickUp,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    monkeypatch.setenv("SPOOLHQ_CLICKUP_TOKEN", TOKEN)
    set_tracker(projects_dir)
    settings = load_settings()
    app = create_app(
        settings,
        token=token,
        agents=Agents(
            implementer=FakeRunner(AGENT_FIXTURES / "success_writes_file.jsonl"),
            reviewer=FakeRunner(REVIEW_FIXTURES / "approve.jsonl"),
        ),
        tracker_transport=server.transport,
    )
    with TestClient(app, base_url=f"http://127.0.0.1:{settings.port}") as test_client:
        yield test_client


def test_routes_need_the_token_and_a_project(client: TestClient, token: str) -> None:
    assert client.get("/api/projects/demo/tracker").status_code == 401
    assert client.post("/api/projects/demo/tracker/push").status_code == 401
    assert client.get("/api/projects/nope/tracker", headers=auth(token)).status_code == 404


def test_without_a_tracker_block(run_client: TestClient, token: str) -> None:
    response = run_client.get("/api/projects/demo/tracker", headers=auth(token))
    assert response.json() == {
        "kind": None,
        "state": "off",
        "pending": 0,
        "last_error": None,
        "last_synced_at": None,
    }
    assert run_client.app.state.tracker._thread is None  # type: ignore[attr-defined]
    push = run_client.post("/api/projects/demo/tracker/push", headers=auth(token))
    assert push.status_code == 409
    assert push.json()["error"]["message"] == "'demo' has no tracker block in project.yaml"


def test_push_then_status(tracker_client: TestClient, token: str, server: FakeClickUp) -> None:
    sync = tracker_client.app.state.tracker  # type: ignore[attr-defined]
    assert sync._thread is not None  # started: the project has a tracker block
    push = tracker_client.post("/api/projects/demo/tracker/push", headers=auth(token))
    assert push.json() == {"queued": 1}
    view = tracker_client.get("/api/projects/demo/tracker", headers=auth(token)).json()
    assert (view["kind"], view["state"], view["pending"]) == ("clickup", "syncing", 1)

    sync.tick("demo")
    view = tracker_client.get("/api/projects/demo/tracker", headers=auth(token)).json()
    assert (view["state"], view["pending"], view["last_error"]) == ("ok", 0, None)
    assert [t.name for t in server.tasks.values()] == ["T07 · Parse slugs"]


@pytest.mark.integration
def test_a_run_merges_while_clickup_hangs(
    tracker_client: TestClient, token: str, server: FakeClickUp, git_repo: Path
) -> None:
    release = threading.Event()
    hanging = threading.Event()

    def hang(request: httpx.Request) -> None:
        hanging.set()
        release.wait(30)

    server.on_request = hang
    server.fail = 500
    sync = tracker_client.app.state.tracker  # type: ignore[attr-defined]
    worker = threading.Thread(target=sync.tick, args=("demo",))
    worker.start()
    assert hanging.wait(5)

    started = time.monotonic()
    assert (
        tracker_client.post("/api/projects/demo/run/next", headers=auth(token)).status_code == 201
    )
    current = follow(tracker_client, token)
    took = time.monotonic() - started

    assert current["run"]["status"] == "done"
    assert run_git(git_repo, "log", "-1", "--format=%s", "main").strip() == "T07: Parse slugs"
    assert took < 15  # never waited on the hung tracker call
    view = tracker_client.get("/api/projects/demo/tracker", headers=auth(token)).json()
    assert view["state"] == "syncing"

    release.set()
    worker.join(10)
    server.on_request, server.fail = None, None
