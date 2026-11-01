"""Ticket endpoints: list and read, edits with ETags (conflicts, round-trip), status
transitions, and unblocking."""

import hashlib
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import Agents
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
    assert put.status_code == 200, put.json()
    assert (fixture_tickets / path.name).read_bytes() == path.read_bytes()
    assert put.headers["ETag"] == got.headers["ETag"]


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
