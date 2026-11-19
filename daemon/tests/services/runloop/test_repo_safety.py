"""The run loop in a repo carrying its own agent settings and git hooks (T42)."""

from pathlib import Path

import pytest

from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import LocalIntegrator, RunLoop
from spoolhq.services.runs import AttemptStatus, EventKind, Run, RunRegistry, RunStatus
from spoolhq.services.tickets import load_ticket
from tests.conftest import commit_file, run_git
from tests.services.agents.test_repo_settings import plant_repo_settings
from tests.services.git.test_hooks import fired, require_hooks_fire, write_hook
from tests.services.runloop.conftest import LoopFactory, ManualClock, Transcripts

GIT_HOOKS = ("pre-commit", "post-checkout", "post-merge", "post-commit", "post-rewrite")


def run_once(loop: RunLoop) -> Run:
    run = loop.start("demo", "next")
    loop.wait("demo")
    return run


def blocked(registry: RunRegistry, run: Run, projects_dir: Path) -> str | None:
    final = registry.get("demo").run_log.get_run(run.id)
    assert final.status is RunStatus.BLOCKED
    assert load_ticket("demo", "T01", projects_dir=projects_dir).meta.status == "blocked"
    return final.reason


def main_sha(repo: Path) -> str:
    return run_git(repo, "rev-parse", "main").strip()


def policy_failed(registry: RunRegistry, run: Run) -> bool:
    return any(
        e.payload.get("step") == "policy" and e.payload.get("state") == "failed"
        for e in registry.get("demo").run_log.events_since(0, run_id=run.id)
        if e.kind is EventKind.STEP
    )


@pytest.mark.parametrize(
    "planted", [".claude/settings.json", ".mcp.json", ".codex/config.toml", "web/.claude/x.md"]
)
def test_an_agent_that_writes_agent_settings_blocks_the_ticket(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    projects_dir: Path,
    repo: Path,
    planted: str,
) -> None:
    before = main_sha(repo)
    reviewer = FakeRunner([])
    loop, gates = make_loop(
        [transcripts.implement({"hello.py": "x = 1\n", planted: '{"allow": ["Bash"]}'})],
        reviewer,
    )

    run = run_once(loop)

    assert blocked(registry, run, projects_dir) == f"The agent changed agent settings: {planted}"
    assert policy_failed(registry, run)
    attempts = registry.get("demo").run_log.list_attempts(run.id)
    assert [a.status for a in attempts] == [AttemptStatus.ERROR]
    assert gates.calls == [] and reviewer.calls == []
    assert main_sha(repo) == before


def test_a_git_ignored_settings_file_blocks_too(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    projects_dir: Path,
    repo: Path,
) -> None:
    # Ignored files are never committed, but would still sit in the next attempt's worktree.
    commit_file(repo, ".gitignore", ".claude/settings.local.json\n", "ignore local settings")
    loop, _ = make_loop(
        [transcripts.implement({".claude/settings.local.json": "{}"})], FakeRunner([])
    )

    run = run_once(loop)

    assert blocked(registry, run, projects_dir) == (
        "The agent changed agent settings: .claude/settings.local.json"
    )


def test_settings_already_in_the_repo_are_not_the_agents(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    tmp_path: Path,
    clock: ManualClock,
) -> None:
    plant_repo_settings(repo, tmp_path / "marker")
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "--quiet", "--no-verify", "-m", "agent settings")
    loop, _ = make_loop(
        [transcripts.implement()],
        [transcripts.review("approve")],
        integrator=LocalIntegrator(clock=clock),
    )

    run = run_once(loop)

    assert registry.get("demo").run_log.get_run(run.id).status is RunStatus.DONE


def test_a_backend_that_cant_exclude_the_repos_settings_never_starts(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    projects_dir: Path,
    repo: Path,
    tmp_path: Path,
) -> None:
    plant_repo_settings(repo, tmp_path / "marker")
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "--quiet", "--no-verify", "-m", "agent settings")
    leaky = FakeRunner(
        [transcripts.implement()], name="leaky", unexcluded_settings=(".claude/settings.json",)
    )
    loop, _ = make_loop(leaky, FakeRunner([]))

    run = run_once(loop)

    assert blocked(registry, run, projects_dir) == (
        "This repo has agent settings SpoolHQ can't override for leaky: .claude/settings.json"
    )
    assert leaky.calls == []


def test_a_full_run_in_a_hostile_repo_merges_and_runs_no_hook(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    projects_dir: Path,
    repo: Path,
    tmp_path: Path,
    clock: ManualClock,
) -> None:
    markers = tmp_path / "markers"
    markers.mkdir()
    plant_repo_settings(repo, markers / "agent-hook")
    hooks = tmp_path / "repo-hooks"
    for name in GIT_HOOKS:
        write_hook(hooks, name, markers)
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "--quiet", "--no-verify", "-m", "agent settings")
    run_git(repo, "config", "core.hooksPath", str(hooks))
    require_hooks_fire(repo, markers)
    run_git(repo, "reset", "--quiet", "--hard", "HEAD~1")  # drop the control commit
    for marker in markers.iterdir():
        marker.unlink()
    before = main_sha(repo)
    loop, _ = make_loop(
        [transcripts.implement()],
        [transcripts.review("approve")],
        integrator=LocalIntegrator(clock=clock),
    )

    run = run_once(loop)

    assert registry.get("demo").run_log.get_run(run.id).status is RunStatus.DONE
    assert load_ticket("demo", "T01", projects_dir=projects_dir).meta.status == "done"
    assert main_sha(repo) != before
    assert fired(markers) == []
