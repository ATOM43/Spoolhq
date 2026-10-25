import threading
from collections.abc import Iterator
from pathlib import Path

import pytest

from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import NotFoundError, PlanJobs, RunActiveError, RunLoopError
from spoolhq.services.runs import AttemptKind, AttemptStatus, RunKind, RunRegistry, RunStatus
from spoolhq.services.tickets import list_tickets
from tests.conftest import DASHBOARD_PLAN, plan_transcript


@pytest.fixture
def registry(projects_dir: Path) -> Iterator[RunRegistry]:
    registry = RunRegistry("test-instance")
    yield registry
    registry.close()


def jobs(registry: RunRegistry, projects_dir: Path, home: Path, runner: FakeRunner) -> PlanJobs:
    return PlanJobs(registry, projects_dir=projects_dir, home=home, runner=runner)


def test_a_plan_run_is_recorded_with_kind_plan_and_its_usage(
    plan_project: Path, projects_dir: Path, home: Path, registry: RunRegistry
) -> None:
    plans = jobs(registry, projects_dir, home, FakeRunner(DASHBOARD_PLAN))
    run = plans.start("demo")
    plans.wait("demo", 30)

    run_log = registry.get("demo").run_log
    done = run_log.get_run(run.id)
    assert (done.kind, done.status, done.reason) == (
        RunKind.PLAN,
        RunStatus.DONE,
        "18 draft tickets written",
    )
    [attempt] = run_log.list_attempts(run.id)
    assert (attempt.kind, attempt.status, attempt.backend) == (
        AttemptKind.PLAN,
        AttemptStatus.APPROVED,
        "fake",
    )
    usage = run_log.run_usage(run.id)
    assert (usage.input_tokens, usage.output_tokens, usage.cache_read_tokens) == (9200, 2500, 3000)
    assert usage.weighted_tokens == 6200 + 2500 + 300  # cache reads count a tenth
    assert (plan_project / attempt.dir / "transcript.jsonl").is_file()
    assert len(list_tickets("demo", projects_dir=projects_dir).tickets) == 18


def test_a_failed_plan_blocks_the_run_with_the_error(
    plan_project: Path, projects_dir: Path, home: Path, registry: RunRegistry, tmp_path: Path
) -> None:
    bad = plan_transcript(tmp_path / "bad.jsonl", "no plan")
    plans = jobs(registry, projects_dir, home, FakeRunner([bad, bad]))
    run = plans.start("demo")
    plans.wait("demo", 30)

    done = registry.get("demo").run_log.get_run(run.id)
    assert done.status is RunStatus.BLOCKED
    assert done.reason == "planner output invalid: no <plan> block in the final message"
    [attempt] = registry.get("demo").run_log.list_attempts(run.id)
    assert attempt.status is AttemptStatus.ERROR


def test_errors_before_the_agent_come_back_at_once(
    workspace: Path, projects_dir: Path, home: Path, registry: RunRegistry
) -> None:
    plans = jobs(registry, projects_dir, home, FakeRunner(DASHBOARD_PLAN))
    with pytest.raises(NotFoundError, match="no project 'nope'"):
        plans.start("nope")
    (workspace / "CONTEXT.md").unlink()
    with pytest.raises(RunLoopError, match="no CONTEXT.md"):
        plans.start("demo")
    with pytest.raises(NotFoundError):
        plans.approve("nope")


def test_one_plan_per_project_at_a_time(
    plan_project: Path, projects_dir: Path, home: Path, registry: RunRegistry
) -> None:
    runner = FakeRunner(DASHBOARD_PLAN)
    plans = jobs(registry, projects_dir, home, runner)
    gate = threading.Event()
    original = runner.run

    def slow(*args: object, **kwargs: object) -> object:
        gate.wait(10)
        return original(*args, **kwargs)  # type: ignore[arg-type]

    runner.run = slow  # type: ignore[method-assign]
    run = plans.start("demo")
    with pytest.raises(
        RunActiveError, match=f"already being generated for 'demo' \\(run {run.id}\\)"
    ):
        plans.start("demo")
    gate.set()
    plans.wait("demo", 30)
    plans.close()


def test_approve_through_the_jobs(
    plan_project: Path, projects_dir: Path, home: Path, registry: RunRegistry
) -> None:
    plans = jobs(registry, projects_dir, home, FakeRunner(DASHBOARD_PLAN))
    with pytest.raises(RunLoopError, match="nothing to approve"):
        plans.approve("demo")
    plans.start("demo")
    plans.wait("demo", 30)
    assert len(plans.approve("demo")) == 18
