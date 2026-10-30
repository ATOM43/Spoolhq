"""Done when 2: a daemon killed during integration never leaves main half-updated, and
startup recovery finishes or undoes the integration, idempotently."""

import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from spoolhq.services.agents import FakeRunner
from spoolhq.services.git import operation_in_progress
from spoolhq.services.projects import load_project
from spoolhq.services.runloop import (
    Agents,
    HoldForIntegration,
    LocalIntegrator,
    RunLoop,
    recover_integrations,
)
from spoolhq.services.runs import (
    IntegrationState,
    RunRegistry,
    RunStatus,
    open_integrations,
    set_integration_state,
    start_integration,
)
from spoolhq.services.tickets import load_ticket
from tests.conftest import commit_file, run_git
from tests.services.runloop.conftest import FakeGates, LoopFactory, Transcripts

DAEMON_DIR = Path(__file__).resolve().parents[3]
BRANCH = "refs/heads/feat/T01-say-hello-t01"
INTERRUPTED = "integration interrupted; run spool run integrate demo T01"


def git(repo: Path, *args: str) -> str:
    return run_git(repo, *args).strip()


@pytest.fixture
def held(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry, repo: Path
) -> str:
    """T01 approved and held, then main moved on; returns that main's sha."""
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=HoldForIntegration()
    )
    loop.start("demo", "next")
    loop.wait("demo")
    loop.close()
    assert registry.get("demo").run_log.list_runs()[0].status is RunStatus.AWAITING_APPROVAL
    return commit_file(repo, "other.py", "y = 1\n", "someone else")


@pytest.fixture
def restart(projects_dir: Path) -> Iterator[Callable[[], RunRegistry]]:
    """The run logs as the next daemon opens them (interrupted runs marked)."""
    registries: list[RunRegistry] = []

    def start() -> RunRegistry:
        registries.append(RunRegistry.start(projects_dir, daemon_instance="after"))
        return registries[-1]

    yield start
    for registry in registries:
        registry.close()


def recover(registry: RunRegistry, projects_dir: Path, worktrees: Path) -> list[str]:
    project = load_project("demo", projects_dir=projects_dir)
    run_log = registry.get("demo").run_log
    return recover_integrations(run_log, project, projects_dir, worktrees)


def ticket_status(projects_dir: Path) -> str:
    return load_ticket("demo", "T01", projects_dir=projects_dir).meta.status


@pytest.mark.integration
@pytest.mark.parametrize("state", ["merging", "committed", "advanced", "tagged"])
def test_crash_after_each_journal_state(
    held: str,
    restart: Callable[[], RunRegistry],
    registry: RunRegistry,
    repo: Path,
    projects_dir: Path,
    worktrees: Path,
    state: str,
) -> None:
    old_main = held
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

    # The main checkout: no operation in progress, HEAD the old main or the new commit.
    journal = open_integrations(registry.get("demo").run_log)
    assert [row.state.value for row in journal] == [state]
    commit = journal[0].commit_sha
    assert operation_in_progress(repo) is None
    main = git(repo, "rev-parse", "main")
    assert main == (commit if state in ("advanced", "tagged") else old_main)
    assert git(repo, "status", "--porcelain") == ""

    after = restart()
    first = recover(after, projects_dir, worktrees)

    log = after.get("demo").run_log
    run = log.list_runs()[0]
    path = worktrees / "demo" / "T01"
    if state in ("merging", "committed"):
        assert first == [f"T01: {INTERRUPTED}"]
        assert (run.status, run.reason) == (RunStatus.AWAITING_APPROVAL, INTERRUPTED)
        assert ticket_status(projects_dir) == "awaiting_approval"
        assert git(path, "symbolic-ref", "HEAD") == BRANCH
        assert git(path, "status", "--porcelain") == ""
        assert git(repo, "tag", "--list") == ""
    else:
        assert commit is not None
        assert first == [f"T01: finished, merged as {commit[:7]}"]
        assert run.status is RunStatus.DONE
        assert ticket_status(projects_dir) == "done"
        assert git(repo, "rev-parse", "ticket/T01^{commit}") == commit
        assert not path.exists()
        assert git(repo, "branch", "--list", "feat/*") == ""
    assert open_integrations(log) == []

    # Recovery again changes nothing.
    events, main = len(log.events_since(0, limit=100_000)), git(repo, "rev-parse", "main")
    assert recover(after, projects_dir, worktrees) == []
    assert len(log.events_since(0, limit=100_000)) == events
    assert git(repo, "rev-parse", "main") == main

    if state in ("merging", "committed"):
        # And the ticket can still be integrated.
        unused = FakeRunner([])
        loop = RunLoop(
            after,
            projects_dir=projects_dir,
            worktrees_dir=worktrees,
            home=Path(os.environ["SPOOLHQ_HOME"]),
            agents=Agents(unused, unused),
            integrator=LocalIntegrator(),
            gates=FakeGates(),
        )
        loop.approve("demo", "T01")
        loop.wait("demo")
        loop.close()
        assert log.get_run(run.id).status is RunStatus.DONE
        assert git(repo, "rev-parse", "main^") == old_main


def _crashed_journal(registry: RunRegistry, repo: Path) -> int:
    """A journal row left in ``committed`` by a crash, its run cut off mid-integration."""
    log = registry.get("demo").run_log
    run = log.list_runs()[0]
    log.set_run_status(run.id, RunStatus.RUNNING)
    main = git(repo, "rev-parse", "main")
    row = start_integration(log, run.id, "T01", "main", main)
    squash = git(repo, "commit-tree", "main^{tree}", "-p", "main", "-m", "T01: Say hello T01")
    set_integration_state(log, row.id, IntegrationState.COMMITTED, commit_sha=squash)
    return run.id


def test_dirty_checkout_after_a_cut_off_fast_forward_is_left_alone(
    held: str,
    restart: Callable[[], RunRegistry],
    registry: RunRegistry,
    repo: Path,
    projects_dir: Path,
    worktrees: Path,
) -> None:
    run_id = _crashed_journal(registry, repo)
    (repo / "README.md").write_text("half-written\n", encoding="utf-8")

    after = restart()
    actions = recover(after, projects_dir, worktrees)

    reason = (
        f"integration interrupted while updating {repo.resolve()}; "
        "check git status there before retrying"
    )
    assert actions == [f"T01: {reason}"]
    run = after.get("demo").run_log.get_run(run_id)
    assert (run.status, run.reason) == (RunStatus.AWAITING_APPROVAL, reason)
    assert (repo / "README.md").read_text(encoding="utf-8") == "half-written\n"
    assert ticket_status(projects_dir) == "awaiting_approval"


def test_a_main_checkout_mid_merge_is_skipped(
    held: str,
    restart: Callable[[], RunRegistry],
    registry: RunRegistry,
    repo: Path,
    projects_dir: Path,
    worktrees: Path,
) -> None:
    _crashed_journal(registry, repo)
    run_git(repo, "switch", "--quiet", "-c", "side", "main~1")
    commit_file(repo, "other.py", "side\n", "side")
    run_git(repo, "switch", "--quiet", "main")
    git_exe = shutil.which("git")
    assert git_exe is not None
    subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [git_exe, "-C", str(repo), "merge", "--no-edit", "side"], capture_output=True, check=False
    )
    assert operation_in_progress(repo) == "merge"

    after = restart()

    assert recover(after, projects_dir, worktrees) == [
        f"T01: skipped, a merge is in progress in {repo.resolve()}"
    ]
    assert len(open_integrations(after.get("demo").run_log)) == 1
    assert operation_in_progress(repo) == "merge"
