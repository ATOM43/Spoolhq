"""The dev fake runner's scenarios, end to end through the API with the real gates."""

import shlex
import shutil
import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from spoolhq.api import create_app
from spoolhq.core.config import load_settings
from spoolhq.devtools import SCENARIOS, dev_agents, fake_runner
from spoolhq.devtools.fake_runner import fill_verdict
from spoolhq.services.projects import load_project, save_project

ClientFactory = Callable[[str], TestClient]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def dev_project(run_project: Path, projects_dir: Path) -> Path:
    """``run_project`` whose test gate is real pytest on ``backend/tests``."""
    project = load_project("demo", projects_dir=projects_dir)
    pytest_cmd = [Path(sys.executable).as_posix(), "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    project.commands.test = shlex.join([*pytest_cmd, "backend/tests"])
    save_project(project, projects_dir=projects_dir)
    return run_project


@pytest.fixture
def dev_client(dev_project: Path, token: str) -> Iterator[ClientFactory]:
    clients: list[TestClient] = []

    def make(scenario: str) -> TestClient:
        settings = load_settings()
        app = create_app(
            settings, token=token, agents=dev_agents(scenario, delay_s=0), fake_runner=scenario
        )
        client = TestClient(app, base_url=f"http://127.0.0.1:{settings.port}")
        clients.append(client.__enter__())
        return client

    yield make
    for client in clients:
        client.__exit__(None, None, None)


def run_next(client: TestClient, token: str) -> dict[str, Any]:
    assert client.post("/api/projects/demo/run/next", headers=auth(token)).status_code == 201
    for _ in range(600):
        current: dict[str, Any] = client.get(
            "/api/projects/demo/runs/current", headers=auth(token)
        ).json()
        if not current["working"]:
            return current
        time.sleep(0.05)
    raise AssertionError("the run did not end")


@pytest.mark.integration
@pytest.mark.parametrize(
    ("scenario", "status", "attempts"),
    [("happy", "done", 1), ("gate-retry", "done", 2), ("review-changes", "done", 2)],
)
def test_scenarios_that_merge(
    dev_client: ClientFactory, token: str, git_repo: Path, scenario: str, status: str, attempts: int
) -> None:
    client = dev_client(scenario)
    current = run_next(client, token)
    assert (current["run"]["status"], current["attempts"]) == (status, attempts)
    merged = (git_repo / "backend" / "tests" / "test_spoolhq_fake.py").read_text(encoding="utf-8")
    assert "raise AssertionError" not in merged
    if scenario == "review-changes":
        assert "test_fake_runner_review_fix" in merged
        reviewer = client.app.state.runloop.agents.reviewer  # type: ignore[attr-defined]
        assert len(reviewer.calls) == 2


@pytest.mark.integration
def test_blocked_fails_the_gates_every_time(
    dev_client: ClientFactory, token: str, git_repo: Path
) -> None:
    current = run_next(dev_client("blocked"), token)
    assert current["run"]["status"] == "blocked"
    assert current["attempts"] == 4  # the first attempt and gate_retries (3)
    assert not (git_repo / "backend").exists()


@pytest.mark.integration
def test_a_scenario_writing_outside_the_worktree_blocks(
    dev_client: ClientFactory,
    token: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenarios = tmp_path / "scenarios"
    shutil.copytree(fake_runner.SCENARIOS_DIR, scenarios)
    implement = scenarios / "implement.jsonl"
    text = implement.read_text(encoding="utf-8")
    implement.write_text(text.replace('"backend/tests/', '"../../escape/'), encoding="utf-8")
    monkeypatch.setattr(fake_runner, "SCENARIOS_DIR", scenarios)

    current = run_next(dev_client("happy"), token)

    assert current["run"]["status"] == "blocked"
    assert current["run"]["reason"].startswith(
        "implementer error: policy not enforced: write outside the worktree: ../../escape/"
    )
    assert not any(tmp_path.rglob("escape"))


def test_plan_gives_a_valid_three_ticket_draft(plan_project: Path, token: str) -> None:
    settings = load_settings()
    app = create_app(settings, token=token, agents=dev_agents("plan", delay_s=0))
    with TestClient(app, base_url=f"http://127.0.0.1:{settings.port}") as client:
        response = client.post("/api/projects/demo/plan/generate", headers=auth(token))
        assert response.status_code == 202
        client.app.state.plans.wait("demo", 30)  # type: ignore[attr-defined]
        plan = client.get("/api/projects/demo/plan", headers=auth(token)).json()
    assert (plan["state"], plan["ticket_count"], plan["problems"]) == ("draft", 3, [])


def test_every_scenario_has_its_transcripts() -> None:
    assert list(SCENARIOS) == ["happy", "gate-retry", "review-changes", "blocked", "plan"]
    for implementer, reviewer in SCENARIOS.values():
        for name in (*implementer, *reviewer, "plan.jsonl"):
            assert (fake_runner.SCENARIOS_DIR / name).is_file()


PROMPT = """<done_when>
1. `just test` passes (checked by the gates: test)

2. parse_slug exists

3. it has tests
</done_when>"""


def test_fill_verdict_fits_the_prompts_items() -> None:
    approve = fill_verdict(PROMPT, '{"items": @@ITEMS@@, "verdict": "approve"}')
    assert approve.count('\\"met\\": true') == 3
    changes = fill_verdict(PROMPT, '{"items": @@ITEMS@@, "verdict": "changes_requested"}')
    # Item 1 is checked by the gates, so item 2 is the unmet one.
    assert '{\\"index\\": 2, \\"met\\": false' in changes
    assert fill_verdict("no list", "@@ITEMS@@") == "[]"
