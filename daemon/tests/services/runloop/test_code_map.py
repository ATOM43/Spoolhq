"""The code map through the run loop: built in the worktree before the first attempt,
updated only when the code changed, cached per project, never committed."""

import logging
from pathlib import Path

import pytest

from spoolhq.services.agents import FakeRunner
from spoolhq.services.codegraph import tool
from spoolhq.services.projects import load_project, save_project
from spoolhq.services.runloop import RunLoop
from spoolhq.services.runs import Run, RunRegistry, RunStatus
from tests.conftest import FakeGraphify, run_git
from tests.services.runloop.conftest import PASSING, LoopFactory, Merging, Transcripts, failing

HELLO = {"hello.py": "def hello():\n    return 'hi'\n"}


def run_once(loop: RunLoop, ticket: str) -> Run:
    run = loop.start("demo", "next", ticket)
    loop.wait("demo")
    return run


def status(registry: RunRegistry, run: Run) -> RunStatus:
    return registry.get("demo").run_log.get_run(run.id).status


def set_code_map_chars(projects_dir: Path, chars: int) -> None:
    settings = load_project("demo", projects_dir=projects_dir)
    context = settings.context.model_copy(update={"code_map_chars": chars})
    save_project(settings.model_copy(update={"context": context}), projects_dir=projects_dir)


@pytest.mark.integration
def test_the_implementer_gets_the_map_and_the_reviewer_never_does(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    fake_graphify: FakeGraphify,
    project: Path,
    repo: Path,
    worktrees: Path,
) -> None:
    implementer = FakeRunner([transcripts.implement(HELLO)])
    reviewer = FakeRunner([transcripts.review("approve")])
    merging = Merging()
    loop, _ = make_loop(implementer, reviewer, integrator=merging)

    run = run_once(loop, "T01")

    assert status(registry, run) is RunStatus.DONE
    [(prompt, _)] = implementer.calls
    assert "\n## Code map\n" in prompt
    assert "### Community 0" in prompt
    [(review_prompt, _)] = reviewer.calls
    assert "code_map" not in review_prompt
    assert "Community 0" not in review_prompt
    # Built from the run's worktree, into the workspace's cache, before the attempt.
    [build] = [call for call in fake_graphify.calls() if call["command"] == "full"]
    assert Path(build["argv"][1]) == worktrees / "demo" / "T01"
    assert (project / ".spoolhq" / "codegraph" / "current.json").is_file()
    # Nothing of the graph in the repository or the ticket's commits.
    assert not (repo / "graphify-out").exists()
    tracked = run_git(repo, "ls-files").splitlines() + run_git(repo, "status", "--short").split()
    assert not [path for path in tracked if "graphify" in path or "codegraph" in path]
    assert merging.commits["T01"] == ["spool: T01 attempt 1"]


@pytest.mark.integration
def test_the_next_run_updates_the_cache_instead_of_rebuilding(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    fake_graphify: FakeGraphify,
) -> None:
    implementer = FakeRunner([transcripts.implement(HELLO), transcripts.implement(HELLO)])
    reviewer = FakeRunner([transcripts.review("approve"), transcripts.review("approve")])
    loop, _ = make_loop(implementer, reviewer, gates=[PASSING, PASSING])

    first = run_once(loop, "T01")
    second = run_once(loop, "T02")

    assert status(registry, first) is status(registry, second) is RunStatus.DONE
    assert fake_graphify.commands() == ["full", "cluster", "update", "cluster"]
    assert all("## Code map" in prompt for prompt, _ in implementer.calls)


@pytest.mark.integration
def test_a_retry_updates_the_map_only_after_the_code_changed(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    fake_graphify: FakeGraphify,
) -> None:
    # Attempt 1 adds hello.py; attempt 2 writes the same file again (no change).
    implementer = FakeRunner([transcripts.implement(HELLO) for _ in range(3)])
    reviewer = FakeRunner([transcripts.review("approve")])
    loop, _ = make_loop(implementer, reviewer, gates=[failing("t::a"), failing("t::a"), PASSING])

    run = run_once(loop, "T01")

    assert status(registry, run) is RunStatus.DONE
    assert len(implementer.calls) == 3
    # Before attempt 1: a full build; before 2: an update (hello.py was committed);
    # before 3: nothing, the code is as it was before attempt 2.
    assert fake_graphify.commands() == ["full", "cluster", "update", "cluster"]
    assert all("## Code map" in prompt for prompt, _ in implementer.calls)


@pytest.mark.integration
def test_without_graphify_the_run_carries_on_with_one_note(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    implementer = FakeRunner([transcripts.implement(HELLO) for _ in range(2)])
    reviewer = FakeRunner([transcripts.review("approve")])
    loop, _ = make_loop(implementer, reviewer, gates=[failing("t::a"), PASSING])

    with caplog.at_level(logging.INFO, logger="spoolhq.services.codegraph"):
        run = run_once(loop, "T01")

    assert status(registry, run) is RunStatus.DONE
    assert not any("## Code map" in prompt for prompt, _ in implementer.calls)
    notes = [r for r in caplog.records if r.getMessage().startswith("no code map")]
    assert len(notes) == 1  # not again before the retry


@pytest.mark.integration
def test_a_hanging_graphify_does_not_hold_up_the_run(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    fake_graphify: FakeGraphify,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tool, "TIMEOUT_S", 1.0)
    fake_graphify.configure(sleep=60)
    implementer = FakeRunner([transcripts.implement(HELLO) for _ in range(2)])
    loop, _ = make_loop(implementer, [transcripts.review("approve")], gates=[failing("t"), PASSING])

    run = run_once(loop, "T01")

    assert status(registry, run) is RunStatus.DONE
    assert not any("## Code map" in prompt for prompt, _ in implementer.calls)
    assert fake_graphify.commands() == ["full"]  # timed out once, not tried again


@pytest.mark.integration
def test_zero_chars_turns_the_map_off(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    fake_graphify: FakeGraphify,
    projects_dir: Path,
) -> None:
    set_code_map_chars(projects_dir, 0)
    implementer = FakeRunner([transcripts.implement(HELLO)])
    loop, _ = make_loop(implementer, [transcripts.review("approve")])

    run = run_once(loop, "T01")

    assert status(registry, run) is RunStatus.DONE
    [(prompt, _)] = implementer.calls
    assert "## Code map" not in prompt
    assert fake_graphify.calls() == []
