"""The notes files through a whole run: the run note, the guard and the writes at merge."""

import json
from pathlib import Path

import pytest

from spoolhq.services.runloop import LocalIntegrator, RunLoop
from spoolhq.services.runs import RunRegistry, RunStatus, attempt_dir
from tests.conftest import commit_file, run_git
from tests.services.runloop.conftest import LoopFactory, ManualClock, Transcripts

AREAS = "general, api, data, ui, infra, testing"
START, END = "<!-- spoolhq:recent:start -->", "<!-- spoolhq:recent:end -->"


def run(loop: RunLoop) -> None:
    loop.start("demo", "next")
    loop.wait("demo")


def merge_one(
    make_loop: LoopFactory, transcripts: Transcripts, clock: ManualClock, *paths: Path
) -> RunLoop:
    implement = list(paths) or [transcripts.implement()]
    reviews = [transcripts.review("approve")] * len(implement)
    loop, _ = make_loop(implement, reviews, integrator=LocalIntegrator(clock=clock))
    run(loop)
    return loop


def show(repo: Path, name: str) -> bytes:
    return run_git(repo, "show", f"main:{name}").encode("utf-8")


def outcome(registry: RunRegistry) -> tuple[RunStatus, str | None, list[tuple[str, str]]]:
    log = registry.get("demo").run_log
    final = log.list_runs()[0]
    attempts = [(a.kind.value, a.status.value) for a in log.list_attempts(final.id)]
    return final.status, final.reason, attempts


@pytest.mark.integration
def test_missing_notes_files_are_created_at_the_first_merge(
    make_loop: LoopFactory, transcripts: Transcripts, clock: ManualClock, repo: Path
) -> None:
    claude_before = (repo / "CLAUDE.md").read_bytes() if (repo / "CLAUDE.md").exists() else None
    merge_one(make_loop, transcripts, clock)
    assert show(repo, "DECISIONS.md") == b"# Decisions\n"
    progress = show(repo, "PROGRESS.md").decode("utf-8")
    assert progress.startswith(f"# Progress\n\n{START}\n\n### T01 ")
    claude_after = (repo / "CLAUDE.md").read_bytes() if (repo / "CLAUDE.md").exists() else None
    assert claude_after == claude_before


@pytest.mark.integration
def test_existing_notes_files_keep_their_bytes(
    make_loop: LoopFactory, transcripts: Transcripts, clock: ManualClock, repo: Path
) -> None:
    progress = "# Our log\n\nKept *exactly*  as is.\n"
    decisions = "# Why\n\nNone yet.\n"  # no entries, so nothing to convert
    claude = "# Rules\n"
    commit_file(repo, "PROGRESS.md", progress, "progress")
    commit_file(repo, "DECISIONS.md", decisions, "decisions")
    commit_file(repo, "CLAUDE.md", claude, "claude")
    merge_one(make_loop, transcripts, clock)
    merged = show(repo, "PROGRESS.md")
    assert merged.startswith(progress.encode("utf-8"))
    assert merged[len(progress) :].startswith(f"\n{START}\n\n### T01 ".encode())
    assert show(repo, "DECISIONS.md") == decisions.encode("utf-8")
    assert show(repo, "CLAUDE.md") == claude.encode("utf-8")
    changed = run_git(repo, "show", "--name-only", "--format=", "main").split()
    assert "DECISIONS.md" not in changed and "CLAUDE.md" not in changed


@pytest.mark.integration
def test_two_decisions_land_in_their_area_files_with_index_lines(
    make_loop: LoopFactory, transcripts: Transcripts, clock: ManualClock, repo: Path
) -> None:
    decisions = [
        {"area": "api", "title": "Routes are plural", "text": "Like the rest.\n# Not a heading"},
        {"area": "data", "title": "Dates in UTC", "text": "Always."},
    ]
    merge_one(make_loop, transcripts, clock, transcripts.implement(decisions=decisions))
    progress = show(repo, "PROGRESS.md").decode("utf-8")
    managed = progress.split(START)[1]
    assert managed.startswith("\n\n### T01 · Say hello T01 (2026-10-18)\n\nAdded hello.\n")
    assert show(repo, "DECISIONS.md").decode("utf-8") == (
        "# Decisions\n\n"
        "001 · Routes are plural · docs/decisions/api.md\n"
        "002 · Dates in UTC · docs/decisions/data.md\n"
    )
    api = show(repo, "docs/decisions/api.md").decode("utf-8")
    assert api.endswith("001. Routes are plural\n    Like the rest.\n     # Not a heading\n")
    data = show(repo, "docs/decisions/data.md").decode("utf-8")
    assert data.endswith("002. Dates in UTC\n    Always.\n")
    changed = run_git(repo, "show", "--name-only", "--format=", "main").split()
    assert {"PROGRESS.md", "DECISIONS.md", "docs/decisions/api.md"} <= set(changed)


@pytest.mark.integration
def test_an_unknown_area_goes_back_with_the_allowed_list(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    repo: Path,
    registry: RunRegistry,
) -> None:
    wrong = transcripts.implement(decisions=[{"area": "billing", "title": "T", "text": ""}])
    loop = merge_one(make_loop, transcripts, clock, wrong, transcripts.implement())
    assert outcome(registry) == (
        RunStatus.DONE,
        None,
        [("initial", "error"), ("gate_retry", "approved")],
    )
    prompt = loop_prompts(loop)[-1]
    assert f"Unknown decision area 'billing'; use one of: {AREAS}" in prompt
    assert "SpoolHQ refused your last attempt" in prompt


@pytest.mark.integration
def test_a_missing_note_is_retried_then_blocks_with_the_fixed_message(
    make_loop: LoopFactory, transcripts: Transcripts, clock: ManualClock, registry: RunRegistry
) -> None:
    missing = [transcripts.implement(final="Done, no note.") for _ in range(4)]
    loop = merge_one(make_loop, transcripts, clock, *missing)
    status, reason, attempts = outcome(registry)
    assert (status, reason) == (
        RunStatus.BLOCKED,
        "The agent didn't return its run note after 3 retries",
    )
    assert attempts == [("initial", "error")] + [("gate_retry", "error")] * 3
    assert "The agent didn't return its run note." in loop_prompts(loop)[1]


@pytest.mark.integration
@pytest.mark.parametrize(
    "path", ["PROGRESS.md", "DECISIONS.md", "docs/progress-archive.md", "docs/decisions/api.md"]
)
def test_an_agent_editing_a_notes_file_goes_back_to_the_agent(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    registry: RunRegistry,
    repo: Path,
    path: str,
) -> None:
    edits = transcripts.implement({path: "# Mine\n", "hello.py": "x = 1\n"})
    loop = merge_one(make_loop, transcripts, clock, edits, *[transcripts.implement()] * 3)
    status, reason, attempts = outcome(registry)
    message = (
        f"The agent edited notes files: {path}; put progress and decisions in the run note instead"
    )
    assert (status, reason) == (RunStatus.BLOCKED, f"{message} after 3 retries")
    assert attempts[0] == ("initial", "error")
    assert message in loop_prompts(loop)[1]
    assert run_git(repo, "log", "--format=%s", "main").splitlines()[0] != "T01: Say hello T01"


@pytest.mark.integration
def test_a_broken_index_blocks_the_ticket(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    registry: RunRegistry,
    repo: Path,
) -> None:
    commit_file(repo, "DECISIONS.md", "001 · Gone · docs/decisions/general.md\n", "index")
    main = run_git(repo, "rev-parse", "main")
    decision = [{"area": "general", "title": "New", "text": "Why."}]
    merge_one(make_loop, transcripts, clock, transcripts.implement(decisions=decision))
    status, reason, _ = outcome(registry)
    assert status is RunStatus.BLOCKED
    assert reason == "The notes files don't match: DECISIONS.md: 1 has no entry in docs/decisions/"
    assert run_git(repo, "rev-parse", "main") == main


def loop_prompts(loop: RunLoop) -> list[str]:
    """The prompts the implementer got, oldest first."""
    implementer = loop.agents.implementer
    return [call[0] for call in implementer.calls]  # type: ignore[attr-defined]


@pytest.mark.integration
def test_a_file_over_the_line_limit_fails_the_gates_and_goes_back(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    registry: RunRegistry,
    repo: Path,
) -> None:
    big = "".join(f"x{i} = {i}\n" for i in range(600))
    too_long = transcripts.implement({"big.py": big})
    split = transcripts.implement({"big.py": "x = 1\n"})
    loop = merge_one(make_loop, transcripts, clock, too_long, split)
    message = "big.py: 600 lines, over the 500-line limit"
    status, _, attempts = outcome(registry)
    assert (status, attempts) == (
        RunStatus.DONE,
        [("initial", "gates_failed"), ("gate_retry", "approved")],
    )
    assert message in loop_prompts(loop)[1]
    log = registry.get("demo").run_log
    first = log.list_attempts(log.list_runs()[0].id)[0]
    gates = json.loads((attempt_dir(first.workspace, first) / "gates.json").read_text("utf-8"))
    assert gates["results"][-1]["name"] == "file_size"
    assert gates["failures"][-1]["output_excerpt"] == message


@pytest.mark.integration
def test_a_flat_project_is_converted_on_its_first_merge(
    make_loop: LoopFactory, transcripts: Transcripts, clock: ManualClock, repo: Path
) -> None:
    flat = "# Why\n\n1. **Plain SQL**: no ORM.\n2. **UTC**\n   Always.\n- **Tabs**: never.\n"
    commit_file(repo, "DECISIONS.md", flat, "flat decisions")
    commit_file(repo, "PROGRESS.md", "# Log\n\n## T00\n\nOld.\n", "flat progress")
    decision = [{"area": "api", "title": "Plural routes", "text": "Why."}]
    merge_one(make_loop, transcripts, clock, transcripts.implement(decisions=decision))
    assert show(repo, "DECISIONS.md").decode("utf-8") == (
        "# Why\n\n"
        "001 · Plain SQL · docs/decisions/general.md\n"
        "002 · UTC · docs/decisions/general.md\n"
        "003 · Tabs · docs/decisions/general.md\n"
        "004 · Plural routes · docs/decisions/api.md\n"
    )
    assert show(repo, "docs/decisions/general.md").decode("utf-8") == (
        "# Decisions · general\n\n001. **Plain SQL**: no ORM.\n\n002. **UTC**\n   Always.\n\n"
        "003. **Tabs**: never.\n"
    )
    progress = show(repo, "PROGRESS.md").decode("utf-8")
    assert progress.startswith(f"# Log\n\n## T00\n\nOld.\n\n{START}\n\n### T01 ")
    body = run_git(repo, "log", "-1", "--format=%B", "main")
    assert "- PROGRESS.md: added the spoolhq:recent markers at the end\n" in body
    assert "- DECISIONS.md: moved 3 entries word for word to docs/decisions/general.md" in body


@pytest.mark.integration
def test_an_unparseable_flat_file_blocks_and_changes_nothing(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    registry: RunRegistry,
    repo: Path,
) -> None:
    commit_file(repo, "DECISIONS.md", "# Why\n\n1. **A** x\nStray text.\n", "flat")
    main = run_git(repo, "rev-parse", "main")
    merge_one(make_loop, transcripts, clock)
    status, reason, _ = outcome(registry)
    assert status is RunStatus.BLOCKED
    assert (
        reason == "DECISIONS.md couldn't be converted: line 4 isn't part of an entry: Stray text."
    )
    assert run_git(repo, "rev-parse", "main") == main
