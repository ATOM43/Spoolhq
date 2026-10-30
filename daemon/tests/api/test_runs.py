"""The run endpoints: token, refusals, and a run through the API with fake agents."""

import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import Agents
from tests.conftest import REVIEW_FIXTURES, run_git

ROUTES = [
    ("POST", "/api/projects/demo/runs"),
    ("POST", "/api/projects/demo/runs/1/pause"),
    ("POST", "/api/projects/demo/runs/1/resume"),
    ("POST", "/api/projects/demo/runs/1/cancel"),
    ("POST", "/api/projects/demo/tickets/T07/integrate"),
    ("POST", "/api/projects/demo/tickets/T07/approve"),
    ("POST", "/api/projects/demo/tickets/T07/reject"),
    ("POST", "/api/projects/demo/tickets/T07/discard"),
    ("GET", "/api/projects/demo/runs/current"),
]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def follow(client: TestClient, token: str) -> dict[str, Any]:
    for _ in range(300):
        current: dict[str, Any] = client.get(
            "/api/projects/demo/runs/current", headers=auth(token)
        ).json()
        if not current["working"]:
            return current
        time.sleep(0.05)
    raise AssertionError("the run did not end")


@pytest.mark.parametrize(("method", "path"), ROUTES)
def test_every_run_route_needs_the_token(
    run_client: TestClient, token: str, method: str, path: str
) -> None:
    assert run_client.request(method, path, json={}).status_code == 401
    assert run_client.request(method, path, json={}, headers=auth("wrong")).status_code == 401


def test_current_with_no_run(run_client: TestClient, token: str) -> None:
    response = run_client.get("/api/projects/demo/runs/current", headers=auth(token))
    assert response.status_code == 200
    assert response.json() == {
        "project": "demo",
        "active": False,
        "working": False,
        "run": None,
        "attempts": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "phases": [],
        "last_merged": None,
    }


@pytest.mark.parametrize(
    ("method", "path", "body", "code", "detail"),
    [
        ("POST", "/api/projects/nope/runs", {}, 404, "no project 'nope'"),
        ("GET", "/api/projects/nope/runs/current", None, 404, "no project 'nope'"),
        (
            "POST",
            "/api/projects/demo/runs",
            {"ticket": "T99"},
            404,
            "ticket T99 not found in 'demo'",
        ),
        ("POST", "/api/projects/demo/runs/1/pause", None, 409, "no active run in 'demo'"),
        ("POST", "/api/projects/demo/runs/1/cancel", None, 409, "no active run in 'demo'"),
        ("POST", "/api/projects/demo/runs/1/resume", None, 409, "nothing to resume in 'demo'"),
        (
            "POST",
            "/api/projects/demo/tickets/T07/integrate",
            None,
            409,
            "T07 is ready, not awaiting approval",
        ),
        (
            "POST",
            "/api/projects/demo/tickets/T07/approve",
            None,
            409,
            "T07 is ready, not awaiting approval",
        ),
        (
            "POST",
            "/api/projects/demo/tickets/T07/reject",
            {"note": "x"},
            409,
            "T07 is ready, not awaiting approval",
        ),
        (
            "POST",
            "/api/projects/demo/tickets/T07/reject",
            {},
            409,
            "say what should change with --note",
        ),
        (
            "POST",
            "/api/projects/demo/tickets/T07/discard",
            None,
            409,
            "T07 is ready; only a blocked ticket or one whose run was interrupted can be discarded",
        ),
    ],
)
def test_refusals_carry_the_message(
    run_client: TestClient,
    token: str,
    method: str,
    path: str,
    body: dict[str, Any] | None,
    code: int,
    detail: str,
) -> None:
    response = run_client.request(method, path, json=body, headers=auth(token))
    assert (response.status_code, response.json()) == (code, {"detail": detail})


@pytest.mark.integration
def test_run_through_the_api_merges_into_main(
    run_client: TestClient, token: str, git_repo: Path
) -> None:
    response = run_client.post(
        "/api/projects/demo/runs", json={"mode": "next"}, headers=auth(token)
    )
    assert response.status_code == 201
    assert response.json()["ticket_id"] == "T07"

    current = follow(run_client, token)

    assert current["run"]["status"] == "done"
    assert current["run"]["policy"] == {"mode": "direct", "rules": [], "summary": ""}
    assert current["attempts"] == 1
    lines = [phase["text"] for phase in current["phases"]]
    assert lines[0] == "T07 · Parse slugs · run 1"
    assert lines[-1] == "T07 · done"
    assert run_git(git_repo, "log", "-1", "--format=%s", "main").strip() == "T07: Parse slugs"
    assert run_git(git_repo, "tag", "--list", "ticket/*").split() == ["ticket/T07"]


@pytest.mark.integration
def test_a_needs_human_run_waits_then_is_rejected_and_approved(
    run_client: TestClient, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    loop = run_client.app.state.runloop  # type: ignore[attr-defined]
    reviewer = FakeRunner(
        [REVIEW_FIXTURES / "needs_human.jsonl", REVIEW_FIXTURES / "approve.jsonl"]
    )
    implementer = loop.agents.implementer
    monkeypatch.setattr(loop, "agents", Agents(implementer, reviewer))
    run_client.post("/api/projects/demo/runs", json={"mode": "next"}, headers=auth(token))
    run = follow(run_client, token)["run"]
    assert run["status"] == "awaiting_approval"
    assert run["policy"]["mode"] == "approval"
    assert [hit["rule"] for hit in run["policy"]["rules"]] == ["needs_human"]
    assert run["policy"]["summary"].startswith("needs you: needs_human (")

    response = run_client.post(
        "/api/projects/demo/tickets/T07/reject", json={"note": "rename it"}, headers=auth(token)
    )
    assert response.status_code == 200
    run = follow(run_client, token)["run"]
    assert run["status"] == "done"
    assert run["policy"] == {"mode": "direct", "rules": [], "summary": ""}
    response = run_client.post("/api/projects/demo/tickets/T07/approve", headers=auth(token))
    assert (response.status_code, response.json()) == (
        409,
        {"detail": "T07 is done, not awaiting approval"},
    )
