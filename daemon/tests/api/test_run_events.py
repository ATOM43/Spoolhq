"""``GET …/runs/{run_id}/events``: a run's stored events, paged, oldest first."""

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from spoolhq.services.runs import AttemptKind, AttemptStatus, EventKind, RunLog


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _log(client: TestClient, workspace: Path) -> RunLog:
    return client.app.state.runs.open(workspace).run_log  # type: ignore[attr-defined,no-any-return]


def _get(client: TestClient, token: str, run_id: int, **query: Any) -> Any:
    url = f"/api/projects/demo/runs/{run_id}/events"
    return client.get(url, params=query, headers=auth(token))


def test_1200_events_come_in_pages_of_500_500_and_200(
    client: TestClient, token: str, workspace: Path
) -> None:
    log = _log(client, workspace)
    run = log.start_run("T01")  # one run.started event
    for n in range(1199):
        log.append_event(run.id, EventKind.LOG, {"message": str(n)})

    seqs: list[int] = []
    sizes: list[int] = []
    after = 0
    while True:
        page = _get(client, token, run.id, after=after, limit=500).json()
        sizes.append(len(page["items"]))
        seqs += [item["seq"] for item in page["items"]]
        if page["next_after"] is None:
            break
        after = page["next_after"]
    assert sizes == [500, 500, 200]
    assert seqs == sorted(seqs) and len(set(seqs)) == 1200
    assert page["items"][0]["ticket"] == "T01"


def test_a_limit_over_2000_is_refused(client: TestClient, token: str, workspace: Path) -> None:
    run = _log(client, workspace).start_run("T01")
    response = _get(client, token, run.id, limit=2001)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "limit_too_large"
    assert _get(client, token, run.id, limit=2000).status_code == 200


def test_attempt_n_gives_its_window_with_the_run_level_events(
    client: TestClient, token: str, workspace: Path
) -> None:
    log = _log(client, workspace)
    run = log.start_run("T01")
    log.append_event(run.id, EventKind.LOG, {"message": "worktree"})
    first = log.start_attempt(run.id, AttemptKind.INITIAL)
    log.finish_attempt(first.id, AttemptStatus.GATES_FAILED)
    second = log.start_attempt(run.id, AttemptKind.GATE_RETRY)
    log.append_event(run.id, EventKind.AGENT_MESSAGE, {"text": "hi"}, second.id)
    log.append_event(run.id, EventKind.LOG, {"message": "integrate"})

    one = _get(client, token, run.id, attempt=1).json()["items"]
    two = _get(client, token, run.id, attempt=2).json()["items"]

    assert [e["type"] for e in one] == ["run.started", "log", "attempt.started", "attempt.finished"]
    assert [(e["type"], e["attempt"]) for e in two] == [
        ("attempt.started", 2),
        ("agent.message", 2),
        ("log", None),
    ]
    after = _get(client, token, run.id, attempt=2, after=two[0]["seq"]).json()["items"]
    assert [e["type"] for e in after] == ["agent.message", "log"]


def test_unknown_run_or_attempt_is_404(client: TestClient, token: str, workspace: Path) -> None:
    run = _log(client, workspace).start_run("T01")
    assert _get(client, token, run.id + 1).status_code == 404
    assert _get(client, token, run.id, attempt=3).status_code == 404
    assert client.get(f"/api/projects/demo/runs/{run.id}/events").status_code == 401
