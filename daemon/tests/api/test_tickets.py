"""Ticket endpoints: list and read, edits with ETags (conflicts, round-trip), status
transitions, and unblocking."""

import hashlib
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import Agents, RunLoopError
from spoolhq.services.runs import AttemptKind, RunLog, RunStatus
from spoolhq.services.tickets import load_ticket, render_ticket
from tests.api.test_runs import follow
from tests.conftest import AGENT_FIXTURES, FIXTURES_DIR, REVIEW_FIXTURES

TICKET_FIXTURES = sorted((FIXTURES_DIR / "tickets").glob("T*.md"))


def auth(token: str, **headers: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", **headers}


def etag(path: Path) -> str:
    return f'"{hashlib.sha256(path.read_bytes()).hexdigest()}"'


@pytest.fixture
def fixture_tickets(workspace: Path) -> Path:
    """``demo`` with every T05 round-trip fixture ticket."""
    tickets = workspace / "tickets"
    for path in TICKET_FIXTURES:
        shutil.copy(path, tickets / path.name)
    return tickets


def test_list_with_filters(client: TestClient, token: str, fixture_tickets: Path) -> None:
    every = client.get("/api/projects/demo/tickets", headers=auth(token)).json()
    assert [t["id"] for t in every["tickets"]] == [p.name[:3] for p in TICKET_FIXTURES]
    assert every["invalid"] == []
    status = every["tickets"][0]["meta"]["status"]
    filtered = client.get(
        "/api/projects/demo/tickets", params={"status": status, "phase": 0}, headers=auth(token)
    ).json()["tickets"]
    assert filtered
    assert all(t["meta"]["status"] == status and t["meta"]["phase"] == 0 for t in filtered)
    bad = client.get("/api/projects/demo/tickets?status=nonsense", headers=auth(token))
    assert (bad.status_code, bad.json()["error"]["field"]) == (422, "status")


def test_listed_tickets_carry_their_runs(
    client: TestClient, token: str, fixture_tickets: Path, workspace: Path
) -> None:
    first, second = (path.name[:3] for path in TICKET_FIXTURES[:2])
    with RunLog(workspace, daemon_instance="test") as log:
        old = log.start_run(first)
        log.record_usage(log.start_attempt(old.id, AttemptKind.INITIAL).id, 100, 20)
        log.set_run_status(old.id, RunStatus.BLOCKED, "gates failed")
        new = log.start_run(first)
        attempt = log.start_attempt(new.id, AttemptKind.INITIAL)
        log.record_usage(attempt.id, 50, 5, cost_micro_usd=840_000)
        log.set_run_status(new.id, RunStatus.AWAITING_APPROVAL, "diff 612 lines > 400")
        plan = log.start_plan_run()
        log.set_run_status(plan.id, RunStatus.DONE, "3 draft tickets written")

    tickets = client.get("/api/projects/demo/tickets", headers=auth(token)).json()["tickets"]

    by_id = {ticket["id"]: ticket for ticket in tickets}
    assert by_id[first]["activity"] == {
        "attempts": 2,
        "tokens": 120,
        "cost_micro_usd": 840_000,
        "run_id": new.id,
        "reason": "diff 612 lines > 400",
    }
    assert by_id[second]["activity"] is None
    assert "plan" not in by_id
    one = client.get(f"/api/projects/demo/tickets/{first}", headers=auth(token)).json()
    assert one["activity"] is None


def test_ticket_ids_are_checked_in_the_path(
    client: TestClient, token: str, fixture_tickets: Path
) -> None:
    for bad in ("T1", "T1234", "x01", "T01x"):
        response = client.get(f"/api/projects/demo/tickets/{bad}", headers=auth(token))
        assert response.status_code == 422, bad
    missing = client.get("/api/projects/demo/tickets/T99", headers=auth(token))
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


@pytest.mark.parametrize("path", TICKET_FIXTURES, ids=lambda p: p.name)
def test_get_then_put_unchanged_is_byte_identical(
    client: TestClient, token: str, fixture_tickets: Path, path: Path
) -> None:
    url = f"/api/projects/demo/tickets/{path.name[:3]}"
    got = client.get(url, headers=auth(token))
    assert got.status_code == 200
    body = got.json()
    put = client.put(
        url,
        json={"meta": body["meta"], "body": body["body"]},
        headers=auth(token, **{"If-Match": got.headers["ETag"]}),
    )
    assert (fixture_tickets / path.name).read_bytes() == path.read_bytes()
    if body["meta"]["status"] in ("running", "awaiting_approval"):
        assert (put.status_code, put.json()["error"]["code"]) == (409, "ticket_locked")
        return
    assert put.status_code == 200, put.json()
    assert put.headers["ETag"] == got.headers["ETag"]


def write_ticket(workspace: Path, ticket_id: str, deps: str, status: str = "ready") -> Path:
    file = workspace / "tickets" / f"{ticket_id}-x.md"
    file.write_text(
        f"---\nid: {ticket_id}\ntitle: Ticket {ticket_id}\nphase: 0\ndepends_on: [{deps}]\n"
        f"status: {status}\nestimate_h: 1\n---\n\n## Done when\n\n- [ ] works\n",
        encoding="utf-8",
    )
    return file


def edit(client: TestClient, token: str, ticket_id: str, **changes: object) -> dict[str, object]:
    """PUT the ticket with ``changes`` to its meta (or ``body``); the response's JSON."""
    url = f"/api/projects/demo/tickets/{ticket_id}"
    got = client.get(url, headers=auth(token))
    body = changes.pop("body", got.json()["body"])
    update = {"meta": {**got.json()["meta"], **changes}, "body": body}
    response = client.put(
        url, json=update, headers=auth(token, **{"If-Match": got.headers["ETag"]})
    )
    return {"status": response.status_code, **response.json()}


@pytest.mark.parametrize(
    ("changes", "field", "message"),
    [
        ({"depends_on": ["T99"]}, "meta.depends_on", "T01 depends on T99, which does not exist"),
        ({"depends_on": ["T03"]}, "meta.depends_on", "cycle: T01 → T03 → T01"),
        ({"body": "## Scope\n\nNothing to check.\n"}, "done_when", "“Done when” needs"),
    ],
    ids=["unknown-dependency", "cycle", "empty-done-when"],
)
def test_an_edit_that_breaks_the_plan_is_422_with_the_field(
    client: TestClient,
    token: str,
    workspace: Path,
    changes: dict[str, object],
    field: str,
    message: str,
) -> None:
    tickets = workspace / "tickets"
    write_ticket(workspace, "T01", "")
    write_ticket(workspace, "T03", "T01", "draft")
    before = {p.name: p.read_bytes() for p in tickets.iterdir()}
    answer = edit(client, token, "T01", **changes)
    error = answer["error"]
    assert isinstance(error, dict)
    assert (answer["status"], error["code"], error["field"]) == (422, "validation_error", field)
    assert error["message"].startswith(message)
    assert {p.name: p.read_bytes() for p in tickets.iterdir()} == before


def test_an_edit_while_running_is_409(client: TestClient, token: str, workspace: Path) -> None:
    file = write_ticket(workspace, "T01", "", "running")
    before = file.read_bytes()
    answer = edit(client, token, "T01", title="Renamed")
    assert answer["status"] == 409
    assert answer["error"] == {"code": "ticket_locked", "message": "T01 is locked while running"}
    assert file.read_bytes() == before


def test_a_title_edit_changes_only_the_title_line(
    client: TestClient, token: str, fixture_tickets: Path
) -> None:
    file = fixture_tickets / "T02-crlf.md"
    before = file.read_bytes()
    answer = edit(client, token, "T02", title="Renamed in the app")
    assert answer["status"] == 200
    assert file.read_bytes() == before.replace(b"Windows line endings", b"Renamed in the app", 1)


def test_conflicting_edit(
    client: TestClient, token: str, fixture_tickets: Path, projects_dir: Path
) -> None:
    file = fixture_tickets / "T02-crlf.md"
    got = client.get("/api/projects/demo/tickets/T02", headers=auth(token))
    first = got.headers["ETag"]
    assert first == etag(file)
    edited = {**got.json()["meta"], "title": "Renamed in the app"}
    update = {"meta": edited, "body": got.json()["body"]}

    file.write_bytes(file.read_bytes().replace(b"\r\n## ", b"\r\nEdited outside.\r\n## ", 1))
    on_disk = file.read_bytes()
    stale = client.put(
        "/api/projects/demo/tickets/T02", json=update, headers=auth(token, **{"If-Match": first})
    )
    assert stale.status_code == 412
    error = stale.json()["error"]
    assert (error["code"], error["etag"]) == ("edit_conflict", etag(file))
    assert "Edited outside." in error["current"]["body"]
    assert file.read_bytes() == on_disk

    missing = client.put("/api/projects/demo/tickets/T02", json=update, headers=auth(token))
    assert (missing.status_code, missing.json()["error"]["code"]) == (428, "precondition_required")
    assert file.read_bytes() == on_disk

    expected = load_ticket("demo", "T02", projects_dir=projects_dir)
    expected.meta.title = "Renamed in the app"
    saved = client.put(
        "/api/projects/demo/tickets/T02",
        json={"meta": edited, "body": expected.body},
        headers=auth(token, **{"If-Match": error["etag"]}),
    )
    assert saved.status_code == 200
    assert file.read_bytes() == render_ticket(expected).encode("utf-8")
    assert saved.headers["ETag"] == etag(file)
    assert saved.json()["meta"]["title"] == "Renamed in the app"


def test_status_changes_follow_the_transition_table(
    client: TestClient, token: str, fixture_tickets: Path
) -> None:
    url = "/api/projects/demo/tickets/T01"
    got = client.get(url, headers=auth(token))
    meta = got.json()["meta"]
    assert meta["status"] != "done"
    response = client.put(
        url,
        json={"meta": {**meta, "status": "done"}, "body": got.json()["body"]},
        headers=auth(token, **{"If-Match": got.headers["ETag"]}),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invalid_transition"
    renamed = client.put(
        url,
        json={"meta": {**meta, "id": "T09"}, "body": got.json()["body"]},
        headers=auth(token, **{"If-Match": got.headers["ETag"]}),
    )
    assert (renamed.status_code, renamed.json()["error"]["code"]) == (422, "validation_error")


def test_unblock_refused_when_not_blocked(run_client: TestClient, token: str) -> None:
    response = run_client.post(
        "/api/projects/demo/tickets/T07/unblock", json={"note": "x"}, headers=auth(token)
    )
    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "not_blocked",
        "message": "T07 is ready, not blocked",
    }


@pytest.mark.integration
def test_unblock_a_blocked_ticket(
    run_client: TestClient, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    loop = run_client.app.state.runloop  # type: ignore[attr-defined]
    implementer = FakeRunner([AGENT_FIXTURES / "success_writes_file.jsonl"] * 4)
    reviews = [REVIEW_FIXTURES / "changes_requested.jsonl"] * 3
    reviewer = FakeRunner([*reviews, REVIEW_FIXTURES / "approve.jsonl"])
    monkeypatch.setattr(loop, "agents", Agents(implementer, reviewer))
    run_client.post("/api/projects/demo/run/next", headers=auth(token))
    assert follow(run_client, token)["run"]["status"] == "blocked"

    response = run_client.post(
        "/api/projects/demo/tickets/T07/unblock",
        json={"note": "keep it short"},
        headers=auth(token),
    )
    assert response.status_code == 200
    assert follow(run_client, token)["run"]["status"] == "done"
    assert "keep it short" in implementer.calls[-1][0]


def test_unblock_passes_the_note_and_reset_retries(
    run_client: TestClient, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    loop = run_client.app.state.runloop  # type: ignore[attr-defined]
    calls: list[tuple[object, ...]] = []

    def unblock(*args: object) -> None:
        calls.append(args)
        raise RunLoopError("stop here")

    monkeypatch.setattr(loop, "unblock", unblock)
    url = "/api/projects/demo/tickets/T07/unblock"
    for body in ({"note": "a"}, {"note": "b", "reset_retries": False}):
        run_client.post(url, json=body, headers=auth(token))
    assert calls == [("demo", "T07", "a", True), ("demo", "T07", "b", False)]
    empty = run_client.post(url, json={"note": ""}, headers=auth(token))
    assert (empty.status_code, empty.json()["error"]["field"]) == (422, "note")


def test_reject_without_a_note_is_422(run_client: TestClient, token: str) -> None:
    url = "/api/projects/demo/tickets/T07/reject"
    response = run_client.post(url, json={}, headers=auth(token))
    assert (response.status_code, response.json()["error"]["field"]) == (422, "note")


@pytest.mark.integration
def test_the_detail_has_the_run_attempts_and_git(run_client: TestClient, token: str) -> None:
    url = "/api/projects/demo/tickets/T07"
    before = run_client.get(url, headers=auth(token)).json()
    assert (before["run"], before["attempts"], before["review_retries_left"]) == (None, [], None)
    assert before["git"]["branch"] is None and before["git"]["commit"] is None
    run_client.post("/api/projects/demo/run/next", headers=auth(token))
    follow(run_client, token)

    detail = run_client.get(url, headers=auth(token)).json()
    assert detail["run"]["status"] == "done"
    assert [(a["number"], a["status"]) for a in detail["attempts"]] == [(1, "approved")]
    assert detail["attempts"][0]["run_id"] == detail["run"]["id"]
    assert detail["review_retries_left"] == 2  # the default limit, none used
    git = detail["git"]
    assert len(git["commit"]) == 40 and git["tag"] == "ticket/T07"
    assert git["commit_url"] is None and git["pr_state"] is None
