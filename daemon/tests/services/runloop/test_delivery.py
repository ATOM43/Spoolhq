"""Direct GitHub delivery through the run loop: a local bare repository stands in for
GitHub (``url.<bare>.insteadOf``), with fake agents and gates."""

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from spoolhq.services.projects import load_project, save_project
from spoolhq.services.runloop import (
    Delivery,
    HoldForIntegration,
    RunLoop,
    recover_integrations,
)
from spoolhq.services.runs import RunLog, RunRegistry, RunStatus, open_integrations
from spoolhq.services.tickets import load_ticket
from tests.conftest import (
    GITHUB_URL,
    commit_file,
    make_github_remote,
    push_elsewhere,
    run_git,
    write_hook,
)
from tests.services.runloop.conftest import (
    LoopFactory,
    ManualClock,
    Transcripts,
)
from tests.services.runloop.test_integration import hooked, on_first
from tests.services.runloop.test_integration_crash import DAEMON_DIR


def git(repo: Path, *args: str) -> str:
    return run_git(repo, *args).strip()


def log_of(registry: RunRegistry) -> RunLog:
    return registry.get("demo").run_log


def status(projects_dir: Path, ticket_id: str = "T01") -> str:
    return load_ticket("demo", ticket_id, projects_dir=projects_dir).meta.status


def run(loop: RunLoop) -> None:
    loop.start("demo", "next")
    loop.wait("demo")


@pytest.fixture
def bare(repo: Path, project: Path, projects_dir: Path, tmp_path: Path) -> Path:
    """``demo`` with ``git.remote`` set; the remote is a bare clone of ``repo``."""
    settings = load_project("demo", projects_dir=projects_dir)
    settings.git.remote = GITHUB_URL
    save_project(settings, projects_dir=projects_dir)
    return make_github_remote(repo, tmp_path / "remote.git")


@pytest.fixture
def mate(bare: Path) -> Callable[[str], str]:
    """``mate(name)``: a teammate pushes a commit adding ``name`` to the remote's main."""
    return lambda name: push_elsewhere(bare, bare.parent / "mate", name, f"add {name}")


@pytest.fixture
def delivery(clock: ManualClock) -> Delivery:
    return Delivery(clock=clock)


@pytest.mark.integration
def test_a_ticket_is_pushed_to_the_remote_then_main_advances(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    delivery: Delivery,
    registry: RunRegistry,
    repo: Path,
    bare: Path,
    projects_dir: Path,
) -> None:
    initial = git(repo, "rev-parse", "main")
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=delivery
    )
    run(loop)

    sha = git(bare, "rev-parse", "main")
    assert git(repo, "rev-parse", "main") == sha
    assert git(bare, "rev-parse", f"{sha}^") == initial
    assert git(bare, "log", "-1", "--format=%s", "main") == "T01: Say hello T01"
    assert git(bare, "rev-parse", "refs/tags/ticket/T01") == sha
    assert status(projects_dir) == "done"
    assert log_of(registry).list_runs()[0].status is RunStatus.DONE
    assert open_integrations(log_of(registry)) == []


@pytest.mark.integration
def test_a_refused_push_blocks_with_the_git_error(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    delivery: Delivery,
    registry: RunRegistry,
    repo: Path,
    bare: Path,
    projects_dir: Path,
) -> None:
    write_hook(bare, "pre-receive", 'echo "policy: main is protected" >&2\nexit 1')
    before = git(repo, "rev-parse", "main")
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=delivery
    )
    run(loop)

    reason = log_of(registry).list_runs()[0].reason or ""
    assert reason.startswith(f"cannot push to {GITHUB_URL}: git push failed (exit 1):")
    assert "policy: main is protected" in reason
    assert "pre-receive hook declined" in reason
    assert status(projects_dir) == "blocked"
    assert git(repo, "rev-parse", "main") == before == git(bare, "rev-parse", "main")
    assert run_git(repo, "tag", "--list").strip() == ""


@pytest.mark.integration
def test_main_moving_on_the_remote_redoes_the_integration(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    repo: Path,
    bare: Path,
    mate: Callable[[str], str],
    projects_dir: Path,
) -> None:
    moved: list[str] = []

    def checkpoint(state: str) -> None:
        if state == "committed" and not moved:
            moved.append(mate("theirs.txt"))  # lands between the fetch and the push

    integrator = Delivery(clock=clock, checkpoint=checkpoint)
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=integrator
    )
    run(loop)

    sha = git(bare, "rev-parse", "main")
    assert git(bare, "rev-parse", f"{sha}^") == moved[0]  # on top of the teammate's commit
    assert git(repo, "rev-parse", "main") == sha
    assert git(bare, "show", "--format=", "--name-only", sha).split() == ["PROGRESS.md", "hello.py"]
    assert status(projects_dir) == "done"


@pytest.mark.integration
def test_main_moving_three_times_blocks(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    registry: RunRegistry,
    bare: Path,
    mate: Callable[[str], str],
    projects_dir: Path,
) -> None:
    count = [0]

    def checkpoint(state: str) -> None:
        if state == "committed":
            count[0] += 1
            mate(f"theirs{count[0]}.txt")

    integrator = Delivery(clock=clock, checkpoint=checkpoint)
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=integrator
    )
    run(loop)

    assert count[0] == 3
    assert log_of(registry).list_runs()[0].reason == "main kept moving during integration"
    assert status(projects_dir) == "blocked"
    assert "T01" not in git(bare, "log", "--format=%s", "main")


@pytest.mark.integration
def test_local_main_ahead_of_the_remote_blocks_and_pushes_nothing(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    delivery: Delivery,
    registry: RunRegistry,
    repo: Path,
    bare: Path,
    projects_dir: Path,
) -> None:
    remote_main = git(bare, "rev-parse", "main")
    mine = commit_file(repo, "mine.txt", "x\n", "my own work")
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=delivery
    )
    run(loop)

    assert log_of(registry).list_runs()[0].reason == (
        f"local main has commits that are not on {GITHUB_URL}; push or reset them first:\n"
        f"  {mine[:7]} my own work"
    )
    assert status(projects_dir) == "blocked"
    assert git(bare, "rev-parse", "main") == remote_main
    assert git(bare, "tag", "--list") == ""
    assert git(repo, "rev-parse", "main") == mine


@pytest.mark.integration
def test_local_main_behind_with_a_dirty_checkout_waits_untouched(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    delivery: Delivery,
    registry: RunRegistry,
    repo: Path,
    bare: Path,
    mate: Callable[[str], str],
    projects_dir: Path,
) -> None:
    before = git(repo, "rev-parse", "main")
    theirs = mate("theirs.txt")
    dirty = repo / "notes.txt"
    implementer, _ = hooked([transcripts.implement()], on_first(lambda: dirty.write_text("wip\n")))
    loop, _ = make_loop(implementer, [transcripts.review("approve")], integrator=delivery)
    run(loop)

    assert status(projects_dir) == "awaiting_approval"
    assert (log_of(registry).list_runs()[0].reason or "").startswith(
        f"main checkout has uncommitted changes in {repo}"
    )
    assert git(repo, "rev-parse", "main") == before
    assert git(bare, "rev-parse", "main") == theirs
    assert dirty.read_text() == "wip\n"

    # Once the checkout is clean, integrating fast-forwards main first, then delivers.
    dirty.unlink()
    loop.approve("demo", "T01")
    loop.wait("demo")
    assert status(projects_dir) == "done"
    sha = git(bare, "rev-parse", "main")
    assert git(repo, "rev-parse", "main") == sha
    assert git(bare, "rev-parse", f"{sha}^") == theirs


@pytest.mark.integration
def test_a_project_without_a_remote_integrates_locally(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    delivery: Delivery,
    repo: Path,
    projects_dir: Path,
) -> None:
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=delivery
    )
    run(loop)
    assert git(repo, "log", "-1", "--format=%s", "main") == "T01: Say hello T01"
    assert git(repo, "rev-parse", "refs/tags/ticket/T01") == git(repo, "rev-parse", "main")
    assert status(projects_dir) == "done"


@pytest.mark.integration
def test_a_crash_after_the_push_is_finished_by_recovery_once(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    bare: Path,
    projects_dir: Path,
    worktrees: Path,
) -> None:
    before = git(repo, "rev-parse", "main")
    crash_at("pushed", make_loop, transcripts, projects_dir, worktrees)
    pushed = git(bare, "rev-parse", "main")
    assert git(repo, "rev-parse", "main") == before  # died before advancing
    [row] = open_integrations(log_of(registry))
    assert (row.state.value, row.commit_sha) == ("pushed", pushed)

    first, second, run_status = recover_twice(projects_dir, worktrees)
    assert first == [f"T01: finished, pushed as {pushed[:7]}"]
    assert second == []
    assert run_status is RunStatus.DONE
    assert git(repo, "rev-parse", "main") == pushed
    assert git(bare, "rev-parse", "refs/tags/ticket/T01") == pushed
    assert status(projects_dir) == "done"
    assert not (worktrees / "demo" / "T01").exists()


@pytest.mark.integration
def test_a_crash_before_the_push_waits_for_another_integration(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    repo: Path,
    bare: Path,
    projects_dir: Path,
    worktrees: Path,
) -> None:
    before = git(bare, "rev-parse", "main")
    crash_at("committed", make_loop, transcripts, projects_dir, worktrees)
    first, second, run_status = recover_twice(projects_dir, worktrees)
    assert first == ["T01: integration interrupted; run spool run integrate demo T01"]
    assert second == []
    assert run_status is RunStatus.AWAITING_APPROVAL
    assert git(bare, "rev-parse", "main") == before == git(repo, "rev-parse", "main")


@pytest.mark.integration
def test_recovery_skips_a_row_while_the_remote_is_unreachable(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    bare: Path,
    projects_dir: Path,
    worktrees: Path,
) -> None:
    crash_at("pushed", make_loop, transcripts, projects_dir, worktrees)
    run_git(repo, "config", f"url.{(bare.parent / 'gone.git').as_posix()}.insteadOf", GITHUB_URL)
    run_git(repo, "config", "--unset", f"url.{bare.as_posix()}.insteadOf")
    first, _, run_status = recover_twice(projects_dir, worktrees)
    assert first[0].startswith(f"T01: skipped, cannot fetch {GITHUB_URL}: git fetch failed")
    assert run_status is RunStatus.INTERRUPTED
    assert [row.state.value for row in open_integrations(log_of(registry))] == ["pushed"]


@pytest.mark.integration
def test_an_unreachable_remote_blocks_the_ticket(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    delivery: Delivery,
    registry: RunRegistry,
    repo: Path,
    bare: Path,
) -> None:
    run_git(repo, "config", "--unset", f"url.{bare.as_posix()}.insteadOf")
    run_git(repo, "config", f"url.{(bare.parent / 'gone.git').as_posix()}.insteadOf", GITHUB_URL)
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=delivery
    )
    run(loop)
    reason = log_of(registry).list_runs()[0].reason or ""
    assert reason.startswith(f"cannot fetch main from {GITHUB_URL}: git fetch failed")


def crash_at(
    state: str,
    make_loop: LoopFactory,
    transcripts: Transcripts,
    projects_dir: Path,
    worktrees: Path,
) -> None:
    """Hold T01 approved, then integrate it in a child process that dies after ``state``."""
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=HoldForIntegration()
    )
    run(loop)
    loop.close()
    child = subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [
            sys.executable,
            "-m",
            "tests.services.runloop.crash_child",
            state,
            str(projects_dir),
            str(worktrees),
        ],
        cwd=DAEMON_DIR,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert child.returncode == 1, child.stderr


def recover_twice(projects_dir: Path, worktrees: Path) -> tuple[list[str], list[str], RunStatus]:
    """Recovery as the next daemon runs it, twice; both reports and the run's status."""
    after = RunRegistry.start(projects_dir, daemon_instance="after")
    try:
        project = load_project("demo", projects_dir=projects_dir)
        run_log = after.get("demo").run_log
        first = recover_integrations(run_log, project, projects_dir, worktrees)
        second = recover_integrations(run_log, project, projects_dir, worktrees)
        return first, second, run_log.list_runs()[0].status
    finally:
        after.close()
