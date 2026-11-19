"""Draft routes: start a draft job, read and cancel it, and save drafts in one batch."""

import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from spoolhq.api import create_app
from spoolhq.core.config import load_settings
from spoolhq.devtools.fake_runner import SCENARIOS_DIR, fill_drafts
from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import Agents
from tests.conftest import AGENT_FIXTURES, REVIEW_FIXTURES
from tests.services.runloop.test_drafting import NotReady

BASE = "/api/projects/demo/tickets"
Factory = Callable[..., TestClient]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_client(run_project: Path, token: str) -> Iterator[Factory]:
    clients: list[TestClient] = []

    def make(planner: FakeRunner | None = None, stall_s: float = 0) -> TestClient:
        agents = Agents(
            implementer=FakeRunner(AGENT_FIXTURES / "success_writes_file.jsonl", stall_s=stall_s),
            reviewer=FakeRunner(REVIEW_FIXTURES / "approve.jsonl"),
            planner=planner or FakeRunner(SCENARIOS_DIR / "plan.jsonl", render=fill_drafts),
        )
        settings = load_settings()
        app = create_app(settings, token=token, agents=agents)
        client = TestClient(app, base_url=f"http://127.0.0.1:{settings.port}")
        clients.append(client.__enter__())
        return client

    yield make
    for client in clients:
        client.__exit__(None, None, None)


def finished(client: TestClient, token: str, job_id: str) -> dict[str, Any]:
    for _ in range(600):
        job: dict[str, Any] = client.get(f"{BASE}/draft/{job_id}", headers=auth(token)).json()
        if job["state"] != "running":
            return job
        time.sleep(0.02)
    raise AssertionError("the draft job did not end")


def test_a_request_gives_one_draft(make_client: Factory, token: str, run_project: Path) -> None:
    client = make_client()
    started = client.post(f"{BASE}/draft", json={"request": "add CSV export"}, headers=auth(token))
    assert started.status_code == 202
    job = finished(client, token, started.json()["job_id"])
    assert (job["state"], job["error"], job["project"]) == ("succeeded", None, "demo")
    [draft] = job["drafts"]
    assert draft == {
        "ref": "D1",
        "title": "add CSV export",
        "scope": "- add CSV export",
        "done_when": ["The change works as the request asks", f"`{_test_cmd(run_project)}` passes"],
        "depends_on": [],
        "estimate_h": 2.0,
        "review_required": False,
        "phase": 0,
        "problems": [],
    }
    assert [p.name for p in (run_project / "tickets").iterdir()] == ["T07-parse-slug.md"]
    runs = client.get("/api/projects/demo/runs?kind=ticket", headers=auth(token)).json()
    assert runs["items"] == []
    every = client.get("/api/projects/demo/runs", headers=auth(token)).json()
    assert [r["kind"] for r in every["items"]] == ["draft"]


def _test_cmd(workspace: Path) -> str:
    from spoolhq.services.projects import load_project

    command = load_project("demo", projects_dir=workspace.parent).commands.test
    assert command is not None
    return command


@pytest.mark.parametrize("request_text", ["", "   ", "x" * 2001])
def test_the_request_is_1_to_2000_characters(
    make_client: Factory, token: str, request_text: str
) -> None:
    response = make_client().post(
        f"{BASE}/draft", json={"request": request_text}, headers=auth(token)
    )
    assert (response.status_code, response.json()["error"]["field"]) == (422, "request")


def test_refused_without_a_ready_agent(make_client: Factory, token: str) -> None:
    client = make_client(planner=NotReady(SCENARIOS_DIR / "plan.jsonl"))
    response = client.post(f"{BASE}/draft", json={"request": "r"}, headers=auth(token))
    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "agent_unavailable",
        "message": "No agent is ready to draft tickets: not logged in",
    }


@pytest.mark.integration
def test_refused_while_a_run_is_going(make_client: Factory, token: str) -> None:
    client = make_client(stall_s=30)
    assert client.post("/api/projects/demo/run/ticket/T07", headers=auth(token)).status_code == 201
    try:
        response = client.post(f"{BASE}/draft", json={"request": "r"}, headers=auth(token))
        assert (response.status_code, response.json()["error"]["code"]) == (409, "run_locked")
        assert "a run is already active in 'demo'" in response.json()["error"]["message"]
    finally:
        client.post("/api/projects/demo/run/cancel", headers=auth(token))


def test_cancel_and_unknown_jobs(make_client: Factory, token: str) -> None:
    planner = FakeRunner(SCENARIOS_DIR / "plan.jsonl", render=fill_drafts, stall_s=60)
    client = make_client(planner=planner)
    job_id = client.post(f"{BASE}/draft", json={"request": "r"}, headers=auth(token)).json()[
        "job_id"
    ]
    cancelled = client.post(f"{BASE}/draft/{job_id}/cancel", headers=auth(token))
    assert (cancelled.status_code, cancelled.json()["state"]) == (200, "cancelled")
    for method, path in (("GET", ""), ("POST", "/cancel")):
        missing = client.request(method, f"{BASE}/draft/{'0' * 32}{path}", headers=auth(token))
        assert (missing.status_code, missing.json()["error"]["code"]) == (404, "not_found")


def batch_item(ref: str, title: str, *deps: str) -> dict[str, Any]:
    return {"ref": ref, "title": title, "done_when": "- [ ] works", "depends_on": list(deps)}


def test_batch_saves_drafts_together(make_client: Factory, token: str, run_project: Path) -> None:
    client = make_client()
    body = {"tickets": [batch_item("D1", "CSV export"), batch_item("D2", "CSV docs", "D1")]}
    response = client.post(f"{BASE}/batch", json=body, headers=auth(token))
    assert response.status_code == 201
    saved = response.json()["tickets"]
    assert [(t["id"], t["meta"]["depends_on"]) for t in saved] == [
        ("T08", []),
        ("T09", ["T08"]),
    ]
    assert (run_project / "tickets" / "T09-csv-docs.md").is_file()


def test_an_invalid_batch_writes_nothing(
    make_client: Factory, token: str, run_project: Path
) -> None:
    client = make_client()
    body = {"tickets": [batch_item("D1", "a"), batch_item("D2", "b", "T99")]}
    response = client.post(f"{BASE}/batch", json=body, headers=auth(token))
    assert response.status_code == 422
    assert response.json()["error"]["field"] == "tickets.1.depends_on"
    assert [p.name for p in (run_project / "tickets").iterdir()] == ["T07-parse-slug.md"]
    too_many = {"tickets": [batch_item(f"D{n}", "x") for n in (1, 2, 3, 3)]}
    assert client.post(f"{BASE}/batch", json=too_many, headers=auth(token)).status_code == 422
