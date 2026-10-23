"""RunLoop: cancel, pause, usage limits, crash resume, discard, the lock and errors."""

import threading
from datetime import timedelta
from pathlib import Path

import pytest

from spoolhq.core.daemon_lock import acquire_lock
from spoolhq.services.agents import AgentPolicy, FakeRunner
from spoolhq.services.git import WorktreeManager
from spoolhq.services.projects import load_project, save_project
from spoolhq.services.runloop import RUN_LOCK, NotFoundError, RunActiveError, RunLoopError
from spoolhq.services.runloop.lock import take_run_lock
from spoolhq.services.runs import AttemptKind, RunLog, RunRegistry, RunStatus, recover_interrupted
from spoolhq.services.scheduler import apply_transition
from spoolhq.services.tickets import load_ticket
from tests.conftest import run_git
from tests.services.runloop.conftest import (
    PASSING,
    Hooked,
    LoopFactory,
    ManualClock,
    Transcripts,
    failing,
    write_ticket,
)


def status(projects_dir: Path, ticket_id: str = "T01") -> str:
    return load_ticket("demo", ticket_id, projects_dir=projects_dir).meta.status


def lock_is_free(workspace: Path) -> bool:
    try:
        take_run_lock(workspace, "demo").release()
    except RunActiveError:
        return False
    return True


# --- cancel and pause --------------------------------------------------------------------


def test_cancel_during_the_implementer_removes_the_worktree(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    projects_dir: Path,
    worktrees: Path,
    repo: Path,
    project: Path,
) -> None:
    holder: list[object] = []
    implementer = Hooked(
        FakeRunner([transcripts.implement()]),
        lambda _policy: holder[0].cancel("demo"),  # type: ignore[attr-defined]
    )
    loop, gates = make_loop(implementer)
    holder.append(loop)

    run = loop.start("demo")
    loop.wait("demo")

    log = registry.get("demo").run_log
    final = log.get_run(run.id)
    assert final.status is RunStatus.CANCELLED
    assert [a.status.value for a in log.list_attempts(run.id)] == ["cancelled"]
    assert status(projects_dir) == "ready"
    assert not (worktrees / "demo" / "T01").exists()
    assert run_git(repo, "branch", "--list", "feat/T01-*").strip() == ""
    assert gates.calls == []
    assert lock_is_free(project)
    assert loop.current("demo").active is False


def test_pause_stops_after_the_current_step_and_resume_continues(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    projects_dir: Path,
    worktrees: Path,
    project: Path,
) -> None:
    holder: list[object] = []
    implementer = Hooked(
        FakeRunner([transcripts.implement(), transcripts.implement()]),
        lambda _policy: holder[0].pause("demo") if len(holder) == 1 else None,  # type: ignore[attr-defined]
    )
    loop, gates = make_loop(implementer, [transcripts.review("approve")])
    holder.append(loop)

    run = loop.start("demo")
    loop.wait("demo")

    log = registry.get("demo").run_log
    assert log.get_run(run.id).status is RunStatus.PAUSED
    assert status(projects_dir) == "running"
    assert (worktrees / "demo" / "T01").is_dir()
    assert gates.calls == []  # stopped before the gates
    assert loop.current("demo").active and not loop.current("demo").working
    assert lock_is_free(project)  # no thread holds it while paused
    with pytest.raises(RunActiveError, match=r"\(T01, run 1\)"):
        loop.start("demo", "next", "T02")
    with pytest.raises(RunLoopError, match="already paused"):
        loop.pause("demo")

    holder.append("resumed")
    loop.resume("demo", run.id)
    loop.wait("demo")

    assert log.get_run(run.id).status is RunStatus.DONE
    assert [(a.kind.value, a.status.value) for a in log.list_attempts(run.id)] == [
        ("initial", "interrupted"),
        ("initial", "approved"),
    ]


def test_cancel_a_paused_run(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    projects_dir: Path,
    worktrees: Path,
) -> None:
    loop, _ = make_loop([transcripts.implement(outcome="usage_limit")])
    run = loop.start("demo")
    loop.wait("demo")
    assert loop.timer.due_at("demo") is not None

    cancelled = loop.cancel("demo", run.id)

    assert cancelled.status is RunStatus.CANCELLED
    assert status(projects_dir) == "ready"
    assert not (worktrees / "demo" / "T01").exists()
    assert loop.timer.due_at("demo") is None
    with pytest.raises(RunLoopError, match="no active run in 'demo'"):
        loop.cancel("demo")


# --- usage limits ------------------------------------------------------------------------


def test_usage_limit_pauses_and_resumes_after_the_reset_without_using_a_retry(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    projects_dir: Path,
    worktrees: Path,
    clock: ManualClock,
) -> None:
    settings = load_project("demo", projects_dir=projects_dir)
    settings.limits.gate_retries = 1
    save_project(settings, projects_dir=projects_dir)
    loop, _ = make_loop(
        [
            transcripts.implement(),
            transcripts.implement(outcome="usage_limit"),
            transcripts.implement(),
        ],
        [transcripts.review("approve")],
        gates=[failing("tests/t.py::test_a"), PASSING],
    )

    run = loop.start("demo")
    loop.wait("demo")

    log = registry.get("demo").run_log
    paused = log.get_run(run.id)
    assert paused.status is RunStatus.PAUSED
    assert paused.reset_at == "2026-10-18T10:00:00.000Z"
    assert status(projects_dir) == "running"
    assert (worktrees / "demo" / "T01").is_dir()

    clock.advance(timedelta(hours=1, seconds=59))  # 10:00:59, not yet reset + 60 s
    assert loop.timer.check() == []
    clock.advance(timedelta(seconds=2))
    assert loop.timer.check() == ["demo"]
    loop.wait("demo")

    assert log.get_run(run.id).status is RunStatus.DONE
    # The cut-off gate retry doesn't count: with one gate retry allowed, the run still passes.
    assert [(a.kind.value, a.status.value) for a in log.list_attempts(run.id)] == [
        ("initial", "gates_failed"),
        ("gate_retry", "interrupted"),
        ("gate_retry", "approved"),
    ]


def test_reviewer_usage_limit_pauses_too(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry
) -> None:
    loop, _ = make_loop([transcripts.implement()], [transcripts.review("", outcome="usage_limit")])

    run = loop.start("demo")
    loop.wait("demo")

    paused = registry.get("demo").run_log.get_run(run.id)
    assert (paused.status, paused.reason) == (RunStatus.PAUSED, "the reviewer hit a usage limit")


# --- crash recovery ----------------------------------------------------------------------


def crashed_run(
    project: Path, repo: Path, worktrees: Path, registry: RunRegistry
) -> tuple[int, Path]:
    """T01 left running by a daemon that died mid-attempt, with a commit in its worktree."""
    with RunLog(project, daemon_instance="old") as old:
        run = old.start_run("T01")
        old.start_attempt(run.id, AttemptKind.INITIAL)
    apply_transition("demo", "T01", "running", projects_dir=project.parent)
    manager = WorktreeManager(repo, "demo", "main", worktrees)
    wt = manager.create("T01", "Say hello T01", run.id)
    (wt.path / "old.py").write_text("from before the crash\n", encoding="utf-8")
    manager.commit_all(wt, "spool: T01 attempt 1")
    assert recover_interrupted(registry.get("demo").run_log)[0].id == run.id
    return run.id, wt.path


def test_resume_after_a_crash_continues_in_the_kept_worktree(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    project: Path,
    repo: Path,
    worktrees: Path,
) -> None:
    run_id, path = crashed_run(project, repo, worktrees, registry)
    seen: list[bool] = []

    def check(policy: AgentPolicy) -> None:
        seen.append(policy.worktree == path and (path / "old.py").is_file())

    loop, _ = make_loop(
        Hooked(FakeRunner([transcripts.implement()]), check), [transcripts.review("approve")]
    )
    with pytest.raises(NotFoundError, match="run 9 is not the run to resume"):
        loop.resume("demo", 9)

    resumed = loop.resume("demo")
    loop.wait("demo")

    log = registry.get("demo").run_log
    assert resumed.id == run_id
    assert seen == [True]
    assert log.get_run(run_id).status is RunStatus.DONE
    assert [(a.number, a.kind.value, a.status.value) for a in log.list_attempts(run_id)] == [
        (1, "initial", "interrupted"),
        (2, "initial", "approved"),
    ]


def test_discard_after_a_crash(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    project: Path,
    repo: Path,
    worktrees: Path,
    projects_dir: Path,
) -> None:
    _, path = crashed_run(project, repo, worktrees, registry)
    loop, _ = make_loop([])

    loop.discard("demo", "T01")

    assert not path.exists()
    assert run_git(repo, "branch", "--list", "feat/T01-*").strip() == ""
    assert status(projects_dir) == "ready"
    with pytest.raises(RunLoopError, match="T01 is ready; only a blocked ticket"):
        loop.discard("demo", "T01")
    with pytest.raises(RunLoopError, match="nothing to resume in 'demo'"):
        loop.resume("demo")


def test_resume_with_the_worktree_gone_blocks(
    make_loop: LoopFactory,
    registry: RunRegistry,
    project: Path,
    repo: Path,
    worktrees: Path,
    projects_dir: Path,
) -> None:
    run_id, _ = crashed_run(project, repo, worktrees, registry)
    WorktreeManager(repo, "demo", "main", worktrees).teardown("T01")
    loop, _ = make_loop([])

    with pytest.raises(RunLoopError, match="the worktree of T01 is gone"):
        loop.resume("demo")

    assert registry.get("demo").run_log.get_run(run_id).status is RunStatus.BLOCKED
    assert status(projects_dir) == "blocked"
    assert lock_is_free(project)


# --- the lock ----------------------------------------------------------------------------


def test_one_run_per_project(
    make_loop: LoopFactory, transcripts: Transcripts, project: Path
) -> None:
    started, release = threading.Event(), threading.Event()

    def hold(_policy: AgentPolicy) -> None:
        started.set()
        release.wait(10)

    loop, _ = make_loop(
        Hooked(FakeRunner([transcripts.implement()]), hold), [transcripts.review("approve")]
    )
    loop.start("demo")
    assert started.wait(10)

    with pytest.raises(RunActiveError) as info:
        loop.start("demo")
    assert str(info.value) == "a run is already active in 'demo' (T01, run 1)"
    assert not lock_is_free(project)

    release.set()
    loop.wait("demo")
    assert lock_is_free(project)


def test_lock_held_by_another_process_is_refused(make_loop: LoopFactory, project: Path) -> None:
    loop, _ = make_loop([])
    with acquire_lock(project / RUN_LOCK):
        with pytest.raises(RunActiveError, match=r"a run is already active in 'demo' \(pid \d+\)"):
            loop.start("demo")


@pytest.mark.parametrize("ending", ["blocked", "exception"])
def test_lock_is_released_when_the_run_ends(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    project: Path,
    ending: str,
) -> None:
    def boom(_policy: AgentPolicy) -> None:
        raise RuntimeError("boom")

    implementer = (
        Hooked(FakeRunner([transcripts.implement()]), boom)
        if ending == "exception"
        else FakeRunner([transcripts.implement(outcome="policy_violation")])
    )
    loop, _ = make_loop(implementer)

    run = loop.start("demo")
    loop.wait("demo")

    final = registry.get("demo").run_log.get_run(run.id)
    assert final.status is RunStatus.BLOCKED
    if ending == "exception":
        assert final.reason == "internal error: boom"
    assert lock_is_free(project)
    assert loop.current("demo").active is False


# --- requests that are refused -------------------------------------------------------------


def test_nothing_to_run_explains_why(make_loop: LoopFactory, project: Path) -> None:
    for ticket_id in ("T01", "T02", "T03"):
        write_ticket(project, ticket_id, status="draft")
    loop, _ = make_loop([])

    with pytest.raises(RunLoopError) as info:
        loop.start("demo")

    assert str(info.value) == (
        "nothing to run in 'demo': the plan is not approved yet: T01, T02, T03 still in draft"
    )
    assert lock_is_free(project)


def test_named_ticket_must_exist_and_be_ready(make_loop: LoopFactory, project: Path) -> None:
    write_ticket(project, "T02", status="draft")
    loop, _ = make_loop([])

    with pytest.raises(NotFoundError, match="ticket T09 not found in 'demo'"):
        loop.start("demo", "next", "T09")
    with pytest.raises(RunLoopError, match="T02 is draft, not ready"):
        loop.start("demo", "next", "T02")
    with pytest.raises(NotFoundError, match="no project 'nope'"):
        loop.start("nope")


def test_dirty_repository_is_refused_before_anything_starts(
    make_loop: LoopFactory, repo: Path, registry: RunRegistry, projects_dir: Path
) -> None:
    (repo / "notes.txt").write_text("wip\n", encoding="utf-8")
    loop, _ = make_loop([])

    with pytest.raises(RunLoopError, match="has uncommitted changes"):
        loop.start("demo")

    assert registry.get("demo").run_log.list_runs() == []
    assert status(projects_dir) == "ready"


def test_pause_and_discard_refusals(
    make_loop: LoopFactory, projects_dir: Path, project: Path
) -> None:
    loop, _ = make_loop([])

    with pytest.raises(RunLoopError, match="no active run in 'demo'"):
        loop.pause("demo")
    with pytest.raises(RunLoopError, match="T01 is ready"):
        loop.discard("demo", "T01")


def test_current_with_no_run(make_loop: LoopFactory) -> None:
    loop, _ = make_loop([])
    current = loop.current("demo")
    assert (current.active, current.working, current.run, current.phases) == (
        False,
        False,
        None,
        (),
    )


def test_current_lists_the_phase_lines(make_loop: LoopFactory, transcripts: Transcripts) -> None:
    loop, _ = make_loop([transcripts.implement()], [transcripts.review("approve")])
    loop.start("demo")
    loop.wait("demo")

    current = loop.current("demo")

    assert current.run is not None and current.run.status is RunStatus.DONE
    assert current.attempts == 1
    lines = [line for _, line in current.phases]
    assert lines[0] == "T01 · Say hello T01 · run 1"
    assert "T01 attempt 1 · gates · ✓ passed" in lines
    assert "T01 attempt 1 · review · approve" in lines
    assert lines[-1] == "T01 · done"
