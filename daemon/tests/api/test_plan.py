"""The plan endpoints: token, generate (202 and a ``plan`` run), approve and its refusals."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from spoolhq.api import create_app
from spoolhq.core.config import load_settings
from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import Agents
from spoolhq.services.runs import RunKind, RunLog, RunStatus
from tests.conftest import DASHBOARD_PLAN, REVIEW_FIXTURES

ROUTES = ["/api/projects/demo/plan", "/api/projects/demo/plan/approve"]


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
    response = plan_client.post("/api/projects/demo/plan", headers=auth(token), json={})

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
        "/api/projects/demo/plan", headers=auth(token), json={"template_description": "x"}
    )
    assert response.status_code == 202
    plan_client.app.state.plans.wait("demo", 30)  # type: ignore[attr-defined]
    assert plan_client.post("/api/projects/demo/plan", headers=auth(token)).status_code == 202
    plan_client.app.state.plans.wait("demo", 30)  # type: ignore[attr-defined]


def test_generate_refusals(plan_client: TestClient, token: str, plan_project: Path) -> None:
    missing = plan_client.post("/api/projects/nope/plan", headers=auth(token))
    assert (missing.status_code, missing.json()) == (404, {"detail": "no project 'nope'"})
    (plan_project / "CONTEXT.md").unlink()
    response = plan_client.post("/api/projects/demo/plan", headers=auth(token))
    assert response.status_code == 409
    assert response.json()["detail"].startswith("no CONTEXT.md in ")


def test_approve_mirrors_the_cli(plan_client: TestClient, token: str, plan_project: Path) -> None:
    nothing = plan_client.post("/api/projects/demo/plan/approve", headers=auth(token))
    assert (nothing.status_code, nothing.json()) == (409, {"detail": "nothing to approve"})

    tickets = plan_project / "tickets"
    for ticket_id, dep in (("T01", "T02"), ("T02", "T01")):
        (tickets / f"{ticket_id}-x.md").write_text(
            f"---\nid: {ticket_id}\ntitle: X\nphase: 0\ndepends_on: [{dep}]\nstatus: draft\n"
            "estimate_h: 2\n---\n",
            encoding="utf-8",
        )
    cycle = plan_client.post("/api/projects/demo/plan/approve", headers=auth(token))
    assert (cycle.status_code, cycle.json()) == (
        409,
        {"detail": "cannot approve the plan: cycle: T01 → T02 → T01"},
    )

    (tickets / "T02-x.md").write_text(
        "---\nid: T02\ntitle: X\nphase: 0\ndepends_on: [T01]\nstatus: draft\nestimate_h: 2\n---\n",
        encoding="utf-8",
    )
    (tickets / "T01-x.md").write_text(
        "---\nid: T01\ntitle: X\nphase: 0\nstatus: draft\nestimate_h: 2\n---\n", encoding="utf-8"
    )
    ok = plan_client.post("/api/projects/demo/plan/approve", headers=auth(token))
    assert (ok.status_code, ok.json()) == (200, {"approved": ["T01", "T02"]})
    missing = plan_client.post("/api/projects/nope/plan/approve", headers=auth(token))
    assert missing.status_code == 404
