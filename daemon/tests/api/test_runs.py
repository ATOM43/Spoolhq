"""The run endpoints: token, refusals, and a run through the API with fake agents."""

import json
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import Agents
from spoolhq.services.runs import AttemptKind, AttemptStatus, RunLog, attempt_dir, write_artifact
from tests.conftest import AGENT_FIXTURES, REVIEW_FIXTURES, run_git

ROUTES = [
    ("POST", "/api/projects/demo/run/next"),
    ("POST", "/api/projects/demo/run/all"),
    ("POST", "/api/projects/demo/run/ticket/T07"),
    ("POST", "/api/projects/demo/run/pause"),
    ("POST", "/api/projects/demo/run/resume"),
    ("POST", "/api/projects/demo/run/cancel"),
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
        "cost_micro_usd": None,
        "phases": [],
        "last_merged": None,
        "latest_seq": 0,
    }


@pytest.mark.parametrize(
    ("method", "path", "body", "code", "detail"),
    [
        ("POST", "/api/projects/nope/run/next", {}, 404, "no project 'nope'"),
        ("GET", "/api/projects/nope/runs/current", None, 404, "no project 'nope'"),
        (
            "POST",
            "/api/projects/demo/run/ticket/T99",
            None,
            404,
            "ticket T99 not found in 'demo'",
        ),
        ("POST", "/api/projects/demo/run/pause?run_id=1", None, 409, "no active run in 'demo'"),
        ("POST", "/api/projects/demo/run/cancel", None, 409, "no active run in 'demo'"),
        ("POST", "/api/projects/demo/run/resume", None, 409, "nothing to resume in 'demo'"),
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
            {"note": " "},
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
    assert response.status_code == code
    assert response.json()["error"]["message"] == detail


@pytest.mark.integration
def test_run_through_the_api_merges_into_main(
    run_client: TestClient, token: str, git_repo: Path
) -> None:
    response = run_client.post("/api/projects/demo/run/next", headers=auth(token))
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
    run_client.post("/api/projects/demo/run/next", headers=auth(token))
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
        {"error": {"code": "conflict", "message": "T07 is done, not awaiting approval"}},
    )


# --- history, one run, artifacts ---------------------------------------------------------


def _log(client: TestClient, workspace: Path) -> RunLog:
    return client.app.state.runs.open(workspace).run_log  # type: ignore[attr-defined,no-any-return]


def test_history_pages_are_stable_under_inserts(
    client: TestClient, token: str, workspace: Path
) -> None:
    log = _log(client, workspace)
    for _ in range(120):
        log.start_run("T01")
    seen: list[int] = []
    sizes: list[int] = []
    cursor: str | None = None
    while True:
        params = {"limit": 50, **({"cursor": cursor} if cursor else {})}
        page = client.get("/api/projects/demo/runs", params=params, headers=auth(token)).json()
        if not seen:
            log.start_run("T01")  # started between page 1 and page 2
        sizes.append(len(page["items"]))
        seen += [run["id"] for run in page["items"]]
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert sizes == [50, 50, 20]
    assert seen == list(range(120, 0, -1))  # newest first, no duplicates, no gaps
    first = client.get("/api/projects/demo/runs", headers=auth(token)).json()
    assert len(first["items"]) == 50 and first["items"][0]["id"] == 121


def test_history_rows_carry_every_table_column(
    client: TestClient, token: str, workspace: Path
) -> None:
    log = _log(client, workspace)
    merged = log.start_run("T01")  # one attempt on an API key: a cost
    attempt = log.start_attempt(merged.id, AttemptKind.INITIAL, backend="fake", model="m")
    log.record_usage(attempt.id, 100, 20, cost_micro_usd=1500)
    log.finish_attempt(attempt.id, AttemptStatus.APPROVED)
    log.set_run_status(merged.id, "done")
    blocked = log.start_run("T02")  # two attempts on a subscription: tokens
    for kind in (AttemptKind.INITIAL, AttemptKind.GATE_RETRY):
        attempt = log.start_attempt(blocked.id, kind, backend="fake")
        log.record_usage(attempt.id, 1000, 200)
        log.finish_attempt(attempt.id, AttemptStatus.GATES_FAILED)
    log.set_run_status(blocked.id, "blocked", "gates failed 2 times")
    cancelled = log.start_run("T03")  # cancelled before its first attempt
    log.set_run_status(cancelled.id, "cancelled")
    log.start_plan_run()

    url = "/api/projects/demo/runs"
    rows = client.get(url, params={"kind": "ticket"}, headers=auth(token)).json()["items"]
    assert [row["ticket_id"] for row in rows] == ["T03", "T02", "T01"]
    assert all(row["ended_at"] >= row["started_at"] for row in rows)
    columns = ("status", "attempts", "last_attempt", "backend", "tokens", "cost_micro_usd")
    assert [tuple(row[c] for c in columns) for row in rows] == [
        ("cancelled", 0, None, None, 0, None),
        ("blocked", 2, 2, "fake", 2400, None),
        ("done", 1, 1, "fake", 0, 1500),
    ]
    assert rows[1]["reason"] == "gates failed 2 times"
    everything = client.get(url, headers=auth(token)).json()["items"]
    assert [row["kind"] for row in everything] == ["plan", "ticket", "ticket", "ticket"]
    bad = client.get(url, params={"kind": "nope"}, headers=auth(token))
    assert bad.status_code == 422


def test_a_run_finishing_between_pages_is_not_repeated(
    client: TestClient, token: str, workspace: Path
) -> None:
    log = _log(client, workspace)
    runs = [log.start_run("T01") for _ in range(5)]
    url = "/api/projects/demo/runs"
    first = client.get(url, params={"limit": 2}, headers=auth(token)).json()
    log.set_run_status(runs[4].id, "done")  # one from page 1 and one from page 2 finish
    log.set_run_status(runs[1].id, "blocked", "x")
    rest = client.get(
        url, params={"limit": 10, "cursor": first["next_cursor"]}, headers=auth(token)
    ).json()
    ids = [row["id"] for row in first["items"] + rest["items"]]
    assert ids == [5, 4, 3, 2, 1]
    assert rest["items"][1]["status"] == "blocked" and rest["next_cursor"] is None


def test_history_refusals(client: TestClient, token: str, workspace: Path) -> None:
    over = client.get("/api/projects/demo/runs?limit=201", headers=auth(token))
    assert (over.status_code, over.json()["error"]["code"]) == (400, "limit_too_large")
    bad = client.get("/api/projects/demo/runs?cursor=nonsense", headers=auth(token))
    assert (bad.status_code, bad.json()["error"]["code"]) == (400, "invalid_cursor")
    missing = client.get("/api/projects/nope/runs", headers=auth(token))
    assert missing.status_code == 404


def test_one_run_with_its_attempts(client: TestClient, token: str, workspace: Path) -> None:
    log = _log(client, workspace)
    run = log.start_run("T01")
    attempt = log.start_attempt(run.id, AttemptKind.INITIAL, backend="fake")
    log.finish_attempt(attempt.id, AttemptStatus.CHANGES_REQUESTED)
    body = client.get(f"/api/projects/demo/runs/{run.id}", headers=auth(token)).json()
    assert body["ticket_id"] == "T01"
    assert [(a["number"], a["status"]) for a in body["attempts"]] == [(1, "changes_requested")]
    missing = client.get("/api/projects/demo/runs/999", headers=auth(token))
    assert (missing.status_code, missing.json()["error"]["code"]) == (404, "not_found")


def test_attempt_artifacts(client: TestClient, token: str, workspace: Path, tmp_path: Path) -> None:
    log = _log(client, workspace)
    run = log.start_run("T01")
    attempt = log.start_attempt(run.id, AttemptKind.INITIAL)
    patch = "diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a\r\n+b\r\n"
    write_artifact(attempt, "diff.patch", patch)
    write_artifact(attempt, "transcript.jsonl", '{"type":"result"}\n')
    base = f"/api/projects/demo/runs/{run.id}/attempts/1"

    diff = client.get(f"{base}/diff", headers=auth(token))
    assert diff.status_code == 200
    (file,) = diff.json()["files"]
    assert (file["path"], file["additions"], file["deletions"]) == ("x.py", 1, 1)
    assert file["patch"] == "@@ -1 +1 @@\n-a\r\n+b\r"  # CRLF kept
    transcript = client.get(f"{base}/transcript", headers=auth(token))
    assert (transcript.status_code, transcript.text) == (200, '{"type":"result"}\n')

    # The step hasn't written it yet, versus no such attempt.
    for name in ("review", "gates"):
        early = client.get(f"{base}/{name}", headers=auth(token))
        assert (early.status_code, early.json()["error"]["code"]) == (404, "not_ready")
    other = client.get(f"/api/projects/demo/runs/{run.id}/attempts/2/diff", headers=auth(token))
    assert (other.status_code, other.json()["error"]["code"]) == (404, "not_found")
    assert client.get(f"{base}/secrets", headers=auth(token)).status_code == 404

    outside = tmp_path / "outside.json"
    outside.write_text('{"secret": true}', encoding="utf-8")
    link = attempt_dir(workspace, attempt) / "review.json"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are not available here")
    linked = client.get(f"{base}/review", headers=auth(token))
    assert linked.status_code == 404
    assert "secret" not in linked.text


def test_attempt_reports(client: TestClient, token: str, workspace: Path) -> None:
    log = _log(client, workspace)
    run = log.start_run("T01")
    attempt = log.start_attempt(run.id, AttemptKind.INITIAL)
    gates = {
        "passed": False,
        "results": [
            {
                "name": "lint",
                "command": "just lint",
                "status": "passed",
                "duration_s": 1.25,
                "excerpt": "",
            },
            {
                "name": "test",
                "command": "just test",
                "status": "timed_out",
                "duration_s": 900,
                "excerpt": "collecting\nFAILED t.py::a",
                "output_truncated": True,
            },
        ],
    }
    write_artifact(attempt, "gates.json", json.dumps(gates))
    review = {
        "verdict": "approve",
        "summary": "ok",
        "items": [
            {"index": 2, "item": "B", "met": True, "reason": "b"},
            {"index": 1, "item": "A", "met": False, "reason": "a"},
        ],
    }
    write_artifact(attempt, "review.json", json.dumps(review))
    base = f"/api/projects/demo/runs/{run.id}/attempts/1"

    body = client.get(f"{base}/gates", headers=auth(token)).json()
    assert body["results"][1] == {
        "name": "test",
        "command": "just test",
        "state": "timed_out",
        "duration_ms": 900_000,
        "output": "collecting\nFAILED t.py::a",
        "first_failure_line": 1,
        "truncated": True,
    }
    assert body["results"][0]["duration_ms"] == 1250
    items = client.get(f"{base}/review", headers=auth(token)).json()["items"]
    assert [i["text"] for i in items] == ["A", "B"]


def _wait_working(client: TestClient, token: str) -> None:
    for _ in range(200):
        if client.get("/api/projects/demo/runs/current", headers=auth(token)).json()["working"]:
            return
        time.sleep(0.02)
    raise AssertionError("the run did not start")


@pytest.mark.integration
def test_pause_resume_and_cancel_through_the_api(
    run_client: TestClient, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    loop = run_client.app.state.runloop  # type: ignore[attr-defined]
    slow = FakeRunner([AGENT_FIXTURES / "success_writes_file.jsonl"] * 2, stall_s=0.3)
    monkeypatch.setattr(loop, "agents", Agents(slow, loop.agents.reviewer))
    run_client.post("/api/projects/demo/run/ticket/T07", headers=auth(token))
    _wait_working(run_client, token)
    paused = run_client.post("/api/projects/demo/run/pause", headers=auth(token))
    assert (paused.status_code, paused.json()["ticket_id"]) == (200, "T07")
    assert follow(run_client, token)["run"]["status"] == "paused"

    resumed = run_client.post("/api/projects/demo/run/resume", headers=auth(token))
    assert resumed.status_code == 200
    _wait_working(run_client, token)
    cancelled = run_client.post("/api/projects/demo/run/cancel", headers=auth(token))
    assert cancelled.status_code == 200
    assert follow(run_client, token)["run"]["status"] == "cancelled"


@pytest.mark.integration
def test_run_all_through_the_api(run_client: TestClient, token: str) -> None:
    response = run_client.post("/api/projects/demo/run/all", headers=auth(token))
    assert (response.status_code, response.json()["ticket_id"]) == (201, "T07")
    assert follow(run_client, token)["run"]["status"] == "done"
    again = run_client.post("/api/projects/demo/run/all", headers=auth(token))
    assert again.status_code == 409
