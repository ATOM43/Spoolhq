"""Agents.for_project: each role starts the backend ``project.yaml`` names for it."""

import itertools
import json
from pathlib import Path

import pytest

from spoolhq.services.agents import ClaudeCliRunner, CodexCliRunner, FakeRunner, backends
from spoolhq.services.projects import load_project, save_project
from spoolhq.services.runloop import Agents, PlanJobs, RunLoop
from spoolhq.services.runs import AttemptKind, RunRegistry, RunStatus
from tests.conftest import (
    CODEX_FIXTURES,
    DASHBOARD_PLAN,
    FakeBackend,
    fake_claude_cmd,
    fake_codex_cmd,
    sandbox_which,
)
from tests.services.runloop.conftest import PASSING, FakeGates, ManualClock, Merging, Transcripts


def set_roles(projects_dir: Path, **roles: str) -> None:
    settings = load_project("demo", projects_dir=projects_dir)
    agents = settings.agents.model_copy(update=roles)
    save_project(settings.model_copy(update={"agents": agents}), projects_dir=projects_dir)


@pytest.mark.integration
def test_each_role_starts_its_own_backend(
    fake_backend: FakeBackend,
    transcripts: Transcripts,
    registry: RunRegistry,
    projects_dir: Path,
    worktrees: Path,
    home: Path,
    clock: ManualClock,
    tmp_path: Path,
) -> None:
    planner = fake_backend("fake-planner", FakeRunner(DASHBOARD_PLAN, name="fake-planner"))
    implementer = fake_backend(
        "fake-implementer", FakeRunner(transcripts.implement(), name="fake-implementer")
    )
    record = tmp_path / "record.json"
    reviewer = ClaudeCliRunner(
        claude_cmd=fake_claude_cmd(transcripts.review("approve"), record),
        platform="linux",
        which=sandbox_which,
        home=tmp_path / "user-home",
    )
    fake_backend("claude-code-cli", reviewer)
    set_roles(
        projects_dir,
        default="fake-planner",
        implementer="fake-implementer",
        reviewer="claude-code-cli",
    )

    roles = Agents.for_project(load_project("demo", projects_dir=projects_dir).agents)
    assert (roles.planner, roles.implementer, roles.reviewer) == (planner, implementer, reviewer)

    loop = RunLoop(
        registry,
        projects_dir=projects_dir,
        worktrees_dir=worktrees,
        home=home,
        integrator=Merging(),
        clock=clock,
        gates=FakeGates([PASSING]),
        poll_s=3600,
    )
    try:
        run = loop.start("demo", "T01")
        loop.wait("demo")
    finally:
        loop.close()

    log = registry.get("demo").run_log
    assert log.get_run(run.id).status is RunStatus.DONE
    [attempt] = log.list_attempts(run.id)
    assert (attempt.kind, attempt.backend) == (AttemptKind.INITIAL, "fake-implementer")
    assert len(implementer.calls) == 1  # type: ignore[attr-defined]
    # The approving review came from the claude binary, with the reviewer's read-only tools.
    argv = json.loads(record.read_text(encoding="utf-8"))["argv"]
    assert argv[argv.index("--tools") + 1] == "Read,Glob,Grep"
    assert planner.calls == []  # type: ignore[attr-defined]

    # The planner, through the daemon's plan jobs, uses agents.default here.
    (projects_dir / "demo" / "CONTEXT.md").write_text("# Spec\n\nA dashboard.\n", "utf-8")
    plans = PlanJobs(registry, projects_dir=projects_dir, home=home)
    plan_run = plans.start("demo")
    plans.wait("demo", 30)
    [plan_attempt] = log.list_attempts(plan_run.id)
    assert plan_attempt.backend == "fake-planner"
    assert planner.calls  # type: ignore[attr-defined]
    assert len(implementer.calls) == 1  # type: ignore[attr-defined]


def codex_review(path: Path) -> Path:
    """A Codex reviewer run approving the three Done-when items."""
    items = [{"index": i, "met": True, "reason": f"item {i} ok"} for i in (1, 2, 3)]
    verdict = json.dumps({"items": items, "verdict": "approve", "summary": "approve."})
    lines = [
        {"type": "thread.started", "thread_id": "review"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {
                "id": "r1",
                "type": "agent_message",
                "text": f"Reviewed.\n<verdict>{verdict}</verdict>",
            },
        },
        {"type": "turn.completed", "usage": {"input_tokens": 500, "output_tokens": 100}},
    ]
    path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
    return path


@pytest.mark.integration
def test_a_ticket_runs_end_to_end_on_codex(
    monkeypatch: pytest.MonkeyPatch,
    registry: RunRegistry,
    projects_dir: Path,
    worktrees: Path,
    home: Path,
    clock: ManualClock,
    tmp_path: Path,
) -> None:
    def codex(scenario: Path, record: str, *options: str) -> CodexCliRunner:
        return CodexCliRunner(
            codex_cmd=fake_codex_cmd(scenario, tmp_path / record, *options),
            platform="linux",
            which=sandbox_which,
            home=tmp_path / "user-home",
            system_config=tmp_path / "no-system-config.toml",
        )

    implementer = codex(
        CODEX_FIXTURES / "success_writes_file.jsonl", "impl.json", "--write", "hello.txt"
    )
    reviewer = codex(codex_review(tmp_path / "review.jsonl"), "review.json")
    # Agents.for_project builds the implementer, the reviewer, then the planner.
    roles = itertools.cycle([implementer, reviewer, implementer])
    monkeypatch.setitem(backends.BACKENDS, "codex-cli", lambda base_url, model: next(roles))
    set_roles(projects_dir, default="codex-cli")

    loop = RunLoop(
        registry,
        projects_dir=projects_dir,
        worktrees_dir=worktrees,
        home=home,
        integrator=(merging := Merging()),
        clock=clock,
        gates=FakeGates([PASSING]),
        poll_s=3600,
    )
    try:
        run = loop.start("demo", "T01")
        loop.wait("demo")
    finally:
        loop.close()

    log = registry.get("demo").run_log
    assert log.get_run(run.id).status is RunStatus.DONE
    [attempt] = log.list_attempts(run.id)
    assert (attempt.kind, attempt.backend) == (AttemptKind.INITIAL, "codex-cli")
    assert merging.calls == ["T01"]
    impl = json.loads((tmp_path / "impl.json").read_text(encoding="utf-8"))
    review = json.loads((tmp_path / "review.json").read_text(encoding="utf-8"))
    assert 'extends=":workspace"' in " ".join(impl["argv"])
    assert 'extends=":workspace"' not in " ".join(review["argv"])  # read-only reviewer
    assert "T01" in impl["stdin"]
