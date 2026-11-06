"""The plan endpoints: token, generate (202 and a ``plan`` run), approve and its refusals."""

import threading
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from spoolhq.api import create_app
from spoolhq.core.config import load_settings
from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import Agents
from spoolhq.services.runloop.planning import _Job
from spoolhq.services.runs import RunKind, RunLog, RunStatus
from tests.conftest import DASHBOARD_PLAN, REVIEW_FIXTURES

ROUTES = ["/api/projects/demo/plan/generate", "/api/projects/demo/plan/approve"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def plan_client(plan_project: Path, token: str) -> Iterator[TestClient]:
    """The app with a planner that replays the dashboard plan."""
    settings = load_settings()
    reviewer = FakeRunner(REVIEW_FIXTURES / "approve.jsonl")
    agents = Agents(implementer=reviewer, reviewer=reviewer, planner=FakeRunner(DASHBOARD_PLAN))
    app = create_app(settings, token=token, agents=agents)
    with TestClient(app, base_url=f"http://127.0.0.1:{settings.port}") as test_client:
        yield test_client


@pytest.mark.parametrize("path", ROUTES)
def test_every_plan_route_needs_the_token(plan_client: TestClient, path: str) -> None:
    assert plan_client.post(path).status_code == 401


def test_generate_returns_202_and_the_run_is_logged_as_a_plan(
    plan_client: TestClient, token: str, plan_project: Path
) -> None:
    response = plan_client.post("/api/projects/demo/plan/generate", headers=auth(token), json={})

    assert response.status_code == 202
    body = response.json()
    assert body["run"]["kind"] == "plan"
    assert body["run"]["status"] == "running"
    plan_client.app.state.plans.wait("demo", 30)  # type: ignore[attr-defined]

    with RunLog.open_read_only(plan_project) as run_log:
        run = run_log.get_run(body["run_id"])
        usage = run_log.run_usage(run.id)
    assert (run.kind, run.status) == (RunKind.PLAN, RunStatus.DONE)
    assert usage.weighted_tokens > 0
    assert len(list((plan_project / "tickets").iterdir())) == 18


def test_generate_without_a_body_and_with_a_template(plan_client: TestClient, token: str) -> None:
    response = plan_client.post(
        "/api/projects/demo/plan/generate", headers=auth(token), json={"template_description": "x"}
    )
    assert response.status_code == 202
    plan_client.app.state.plans.wait("demo", 30)  # type: ignore[attr-defined]
    assert (
        plan_client.post("/api/projects/demo/plan/generate", headers=auth(token)).status_code == 202
    )
    plan_client.app.state.plans.wait("demo", 30)  # type: ignore[attr-defined]


def test_generate_refusals(plan_client: TestClient, token: str, plan_project: Path) -> None:
    missing = plan_client.post("/api/projects/nope/plan/generate", headers=auth(token))
    assert (missing.status_code, missing.json()) == (
        404,
        {"error": {"code": "not_found", "message": "no project 'nope'"}},
    )
    (plan_project / "CONTEXT.md").unlink()
    response = plan_client.post("/api/projects/demo/plan/generate", headers=auth(token))
    assert response.status_code == 409
    assert response.json()["error"]["message"].startswith("no CONTEXT.md in ")


def ticket(
    tickets: Path,
    ticket_id: str,
    deps: str = "",
    *,
    status: str = "draft",
    done_when: bool = True,
    name: str = "x",
) -> Path:
    path = tickets / f"{ticket_id}-{name}.md"
    body = "\n## Done when\n\n- [ ] it works\n" if done_when else "\n## Scope\n\n- x\n"
    path.write_text(
        f"---\nid: {ticket_id}\ntitle: X\nphase: 0\ndepends_on: [{deps}]\nstatus: {status}\n"
        f"estimate_h: 2.5\n---\n{body}",
        encoding="utf-8",
    )
    return path


def get_plan(client: TestClient, token: str) -> dict[str, object]:
    response = client.get("/api/projects/demo/plan", headers=auth(token))
    assert response.status_code == 200
    body: dict[str, object] = response.json()
    return body


def test_the_plan_route_needs_the_token(plan_client: TestClient) -> None:
    assert plan_client.get("/api/projects/demo/plan").status_code == 401


def test_plan_summary_none_draft_and_approved(
    plan_client: TestClient, token: str, plan_project: Path
) -> None:
    assert get_plan(plan_client, token) == {
        "state": "none",
        "generated_at": None,
        "ticket_count": 0,
        "total_h": 0.0,
        "problems": [],
    }
    response = plan_client.post("/api/projects/demo/plan/generate", headers=auth(token))
    assert response.status_code == 202
    plan_client.app.state.plans.wait("demo", 30)  # type: ignore[attr-defined]

    draft = get_plan(plan_client, token)
    assert (draft["state"], draft["ticket_count"], draft["problems"]) == ("draft", 18, [])
    assert isinstance(draft["generated_at"], str)
    assert draft["total_h"] == sum(
        float(line.split(":")[1])
        for path in (plan_project / "tickets").iterdir()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("estimate_h:")
    )

    ok = plan_client.post("/api/projects/demo/plan/approve", headers=auth(token))
    assert ok.status_code == 200
    approved = get_plan(plan_client, token)
    assert (approved["state"], approved["ticket_count"]) == ("approved", 18)
    assert approved["generated_at"] == draft["generated_at"]
    missing = plan_client.get("/api/projects/nope/plan", headers=auth(token))
    assert missing.status_code == 404


def test_planning_while_the_planner_runs(plan_client: TestClient, token: str) -> None:
    plans = plan_client.app.state.plans  # type: ignore[attr-defined]
    release = threading.Event()
    worker = threading.Thread(target=release.wait, daemon=True)
    worker.start()
    plans._jobs["demo"] = _Job(1, worker, threading.Event())
    try:
        assert get_plan(plan_client, token)["state"] == "planning"
    finally:
        release.set()
        worker.join()
    assert get_plan(plan_client, token)["state"] == "none"


def test_each_problem_has_its_code_and_ticket_ids(
    plan_client: TestClient, token: str, plan_project: Path
) -> None:
    tickets = plan_project / "tickets"
    tickets.mkdir(exist_ok=True)
    ticket(tickets, "T01", "T03")
    ticket(tickets, "T02", "T01")
    ticket(tickets, "T03", "T02")
    ticket(tickets, "T04", "T99")
    ticket(tickets, "T05", name="a")
    ticket(tickets, "T05", name="b")
    ticket(tickets, "T06", done_when=False)
    ticket(tickets, "T07", status="done", done_when=False)  # done: nothing left to review

    problems = get_plan(plan_client, token)["problems"]
    assert problems == [
        {
            "code": "unknown_dependency",
            "message": "T04 depends on T99, which does not exist",
            "ticket_ids": ["T04", "T99"],
        },
        {
            "code": "cycle",
            "message": "cycle: T01 → T02 → T03 → T01",
            "ticket_ids": ["T01", "T02", "T03"],
        },
        {
            "code": "duplicate_id",
            "message": "T05 is defined in T05-a.md and T05-b.md",
            "ticket_ids": ["T05"],
        },
        {"code": "missing_done_when", "message": "T06 has no 'Done when'", "ticket_ids": ["T06"]},
    ]


def test_an_invalid_ticket_file_is_a_problem(
    plan_client: TestClient, token: str, plan_project: Path
) -> None:
    tickets = plan_project / "tickets"
    tickets.mkdir(exist_ok=True)
    ticket(tickets, "T01")
    (tickets / "T02-x.md").write_text("---\nid: T02\n---\n", encoding="utf-8")

    problems = get_plan(plan_client, token)["problems"]
    assert isinstance(problems, list)
    assert [(p["code"], p["ticket_ids"]) for p in problems] == [("invalid_ticket", ["T02"])]


def test_approve_with_problems_is_409_and_changes_nothing(
    plan_client: TestClient, token: str, plan_project: Path
) -> None:
    tickets = plan_project / "tickets"
    tickets.mkdir(exist_ok=True)
    files = [ticket(tickets, "T01", "T02"), ticket(tickets, "T02", "T01")]
    files.append(ticket(tickets, "T03", done_when=False))
    before = {path: path.read_bytes() for path in files}

    response = plan_client.post("/api/projects/demo/plan/approve", headers=auth(token))

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "plan_invalid"
    assert error["message"] == (
        "cannot approve the plan: cycle: T01 → T02 → T01; T03 has no 'Done when'"
    )
    assert error["problems"] == get_plan(plan_client, token)["problems"]
    assert [p["code"] for p in error["problems"]] == ["cycle", "missing_done_when"]
    assert {path: path.read_bytes() for path in files} == before


def test_a_clean_approve_makes_the_drafts_ready(
    plan_client: TestClient, token: str, plan_project: Path
) -> None:
    nothing = plan_client.post("/api/projects/demo/plan/approve", headers=auth(token))
    assert (nothing.status_code, nothing.json()) == (
        409,
        {"error": {"code": "conflict", "message": "nothing to approve"}},
    )
    tickets = plan_project / "tickets"
    tickets.mkdir(exist_ok=True)
    ticket(tickets, "T01")
    ticket(tickets, "T02", "T01")

    ok = plan_client.post("/api/projects/demo/plan/approve", headers=auth(token))

    assert (ok.status_code, ok.json()) == (200, {"approved": ["T01", "T02"]})
    for path in tickets.iterdir():
        assert "status: ready\n" in path.read_text(encoding="utf-8")
    missing = plan_client.post("/api/projects/nope/plan/approve", headers=auth(token))
    assert missing.status_code == 404
