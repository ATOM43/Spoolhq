"""Draft jobs on the daemon: the job's life, its ``draft`` run and usage, and the
refusals before it starts."""

import dataclasses
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest

from spoolhq.devtools.fake_runner import SCENARIOS_DIR, fill_drafts
from spoolhq.services.agents import BackendInfo, FakeRunner
from spoolhq.services.planner import UNREADABLE
from spoolhq.services.runloop import (
    AgentNotReadyError,
    DraftJobs,
    NotFoundError,
    PlanJobs,
    RunActiveError,
    RunLoop,
)
from spoolhq.services.runs import (
    AttemptKind,
    RunKind,
    RunRegistry,
    RunStatus,
    page_runs,
    project_totals,
)
from tests.conftest import DASHBOARD_PLAN, PLANNER_FIXTURES, plan_transcript


class NotReady(FakeRunner):
    def detect(self) -> BackendInfo:
        return dataclasses.replace(super().detect(), logged_in=False, reason="not logged in")


@pytest.fixture
def registry() -> Iterator[RunRegistry]:
    registry = RunRegistry("test-instance")
    yield registry
    registry.close()


class Clock:
    now = 0.0

    def __call__(self) -> float:
        return self.now


def make_jobs(
    registry: RunRegistry,
    projects_dir: Path,
    home: Path,
    tmp_path: Path,
    runner: FakeRunner,
    plans: PlanJobs | None = None,
    clock: Clock | None = None,
) -> DraftJobs:
    loop = RunLoop(registry, projects_dir=projects_dir, worktrees_dir=tmp_path / "wt", home=home)
    plans = plans or PlanJobs(registry, projects_dir=projects_dir, home=home, runner=runner)
    return DraftJobs(
        registry,
        projects_dir=projects_dir,
        home=home,
        loop=loop,
        plans=plans,
        runner=runner,
        clock=clock or Clock(),
    )


def dev_runner(**kwargs: float) -> FakeRunner:
    return FakeRunner(SCENARIOS_DIR / "plan.jsonl", render=fill_drafts, **kwargs)


def test_a_job_drafts_records_a_draft_run_and_writes_no_tickets(
    run_project: Path, projects_dir: Path, home: Path, registry: RunRegistry, tmp_path: Path
) -> None:
    before = sorted(path.name for path in (run_project / "tickets").iterdir())
    drafts = make_jobs(registry, projects_dir, home, tmp_path, dev_runner())
    job = drafts.start("demo", "split: add CSV export")
    assert job.state == "running"
    done = drafts.wait("demo", job.id, 30)
    assert (done.state, done.error) == ("succeeded", None)
    assert [(d.ref, d.depends_on) for d in done.drafts] == [("D1", ()), ("D2", ("D1",))]
    assert sorted(path.name for path in (run_project / "tickets").iterdir()) == before

    run_log = registry.get("demo").run_log
    run = run_log.get_run(done.run_id)
    assert (run.kind, run.ticket_id, run.status, run.reason) == (
        RunKind.DRAFT,
        "draft",
        RunStatus.DONE,
        "2 draft tickets",
    )
    [attempt] = run_log.list_attempts(run.id)
    assert attempt.kind is AttemptKind.DRAFT
    assert (run_project / attempt.dir / "transcript.jsonl").is_file()
    usage = run_log.run_usage(run.id)
    assert usage.input_tokens > 0
    assert project_totals(run_log).tokens == usage.input_tokens + usage.output_tokens
    assert page_runs(run_log, None, 50, RunKind.TICKET).runs == []
    assert [r.id for r in page_runs(run_log, None, 50).runs] == [run.id]


def test_an_unreadable_answer_fails_the_job(
    run_project: Path, projects_dir: Path, home: Path, registry: RunRegistry, tmp_path: Path
) -> None:
    bad = plan_transcript(tmp_path / "bad.jsonl", "<drafts>nope</drafts>")
    drafts = make_jobs(registry, projects_dir, home, tmp_path, FakeRunner([bad, bad]))
    done = drafts.wait("demo", drafts.start("demo", "r").id, 30)
    assert (done.state, done.error, done.drafts) == ("failed", UNREADABLE, ())
    run = registry.get("demo").run_log.get_run(done.run_id)
    assert (run.status, run.reason) == (RunStatus.BLOCKED, UNREADABLE)


def test_cancel_stops_the_agent(
    run_project: Path, projects_dir: Path, home: Path, registry: RunRegistry, tmp_path: Path
) -> None:
    drafts = make_jobs(registry, projects_dir, home, tmp_path, dev_runner(stall_s=60))
    job = drafts.start("demo", "r")
    cancelled = drafts.cancel("demo", job.id)
    assert (cancelled.state, cancelled.error, cancelled.drafts) == ("cancelled", None, ())
    run = registry.get("demo").run_log.get_run(job.run_id)
    assert run.status is RunStatus.CANCELLED


def test_refused_without_a_ready_agent(
    run_project: Path, projects_dir: Path, home: Path, registry: RunRegistry, tmp_path: Path
) -> None:
    runner = NotReady(SCENARIOS_DIR / "plan.jsonl")
    drafts = make_jobs(registry, projects_dir, home, tmp_path, runner)
    with pytest.raises(AgentNotReadyError, match="No agent is ready to draft tickets: not logged"):
        drafts.start("demo", "r")
    assert runner.calls == []
    assert not (run_project / ".spoolhq" / "state.db").exists()


def test_refused_while_planning(
    run_project: Path, projects_dir: Path, home: Path, registry: RunRegistry, tmp_path: Path
) -> None:
    (run_project / "CONTEXT.md").write_text(
        (PLANNER_FIXTURES / "CONTEXT.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    slow = FakeRunner(DASHBOARD_PLAN, stall_s=60)
    plans = PlanJobs(registry, projects_dir=projects_dir, home=home, runner=slow)
    drafts = make_jobs(registry, projects_dir, home, tmp_path, dev_runner(), plans=plans)
    plans.start("demo")
    try:
        with pytest.raises(RunActiveError, match="a plan is being generated for 'demo'"):
            drafts.start("demo", "r")
    finally:
        plans.close()


def test_unknown_jobs_and_projects(
    run_project: Path, projects_dir: Path, home: Path, registry: RunRegistry, tmp_path: Path
) -> None:
    clock = Clock()
    drafts = make_jobs(registry, projects_dir, home, tmp_path, dev_runner(), clock=clock)
    with pytest.raises(NotFoundError, match="no project 'nope'"):
        drafts.start("nope", "r")
    job = drafts.wait("demo", drafts.start("demo", "r").id, 30)
    with pytest.raises(NotFoundError):
        drafts.get("other", job.id)
    with pytest.raises(NotFoundError):
        drafts.cancel("demo", "0" * 32)
    clock.now = 3599
    assert drafts.get("demo", job.id).state == "succeeded"
    clock.now = 3601  # kept one hour after it ended
    with pytest.raises(NotFoundError):
        drafts.get("demo", job.id)
    drafts.close()


def test_close_cancels_running_jobs(
    run_project: Path, projects_dir: Path, home: Path, registry: RunRegistry, tmp_path: Path
) -> None:
    drafts = make_jobs(registry, projects_dir, home, tmp_path, dev_runner(stall_s=60))
    job = drafts.start("demo", "r")
    done = threading.Event()
    threading.Thread(target=lambda: (drafts.close(), done.set()), daemon=True).start()
    assert done.wait(15)
    assert drafts.get("demo", job.id).state == "cancelled"
