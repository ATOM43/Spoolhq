"""The repo's notes files at a merge: created only when missing, otherwise appended to."""

from pathlib import Path

import pytest

from spoolhq.services.runloop import LocalIntegrator, RunLoop
from tests.conftest import commit_file, run_git
from tests.services.runloop.conftest import LoopFactory, ManualClock, Transcripts


def run(loop: RunLoop) -> None:
    loop.start("demo", "next")
    loop.wait("demo")


def merge_one(make_loop: LoopFactory, transcripts: Transcripts, clock: ManualClock) -> None:
    integrator = LocalIntegrator(clock=clock)
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=integrator
    )
    run(loop)


def show(repo: Path, name: str) -> bytes:
    return run_git(repo, "show", f"main:{name}").encode("utf-8")


@pytest.mark.integration
def test_missing_notes_files_are_created_at_the_first_merge(
    make_loop: LoopFactory, transcripts: Transcripts, clock: ManualClock, repo: Path
) -> None:
    claude_before = (repo / "CLAUDE.md").read_bytes() if (repo / "CLAUDE.md").exists() else None
    merge_one(make_loop, transcripts, clock)
    assert show(repo, "DECISIONS.md") == b"# Decisions\n"
    assert show(repo, "PROGRESS.md").startswith(b"# Progress\n\n## T01 ")
    claude_after = (repo / "CLAUDE.md").read_bytes() if (repo / "CLAUDE.md").exists() else None
    assert claude_after == claude_before


@pytest.mark.integration
def test_existing_notes_files_are_only_appended_to(
    make_loop: LoopFactory, transcripts: Transcripts, clock: ManualClock, repo: Path
) -> None:
    progress = "# Our log\n\nKept *exactly*  as is.\n"
    decisions = "# Why\n\n1. Because.\n"
    claude = "# Rules\n"
    commit_file(repo, "PROGRESS.md", progress, "progress")
    commit_file(repo, "DECISIONS.md", decisions, "decisions")
    commit_file(repo, "CLAUDE.md", claude, "claude")
    merge_one(make_loop, transcripts, clock)
    merged = show(repo, "PROGRESS.md")
    assert merged.startswith(progress.encode("utf-8"))
    assert merged[len(progress) :].startswith(b"\n## T01 ")
    assert show(repo, "DECISIONS.md") == decisions.encode("utf-8")
    assert show(repo, "CLAUDE.md") == claude.encode("utf-8")
    changed = run_git(repo, "show", "--name-only", "--format=", "main").split()
    assert "DECISIONS.md" not in changed and "CLAUDE.md" not in changed
