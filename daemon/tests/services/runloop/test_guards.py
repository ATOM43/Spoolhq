"""The notes guard: only the attempts' own changes to the notes files count."""

from pathlib import Path
from types import SimpleNamespace
from typing import cast

from spoolhq.services.runloop.guards import attempt_message, edited_notes
from spoolhq.services.runloop.model import RunContext
from tests.conftest import commit_file, run_git


def ctx(repo: Path, base: str) -> RunContext:
    worktree = SimpleNamespace(path=repo, base_sha=base)
    return cast(RunContext, SimpleNamespace(worktree=worktree, ticket_id="T01"))


def branch(repo: Path) -> str:
    """``main`` with a PROGRESS.md, then a ``feat`` branch checked out; its base."""
    base = commit_file(repo, "PROGRESS.md", "# Progress\n", "notes")
    run_git(repo, "checkout", "--quiet", "-b", "feat")
    return base


def test_an_attempt_editing_a_notes_file_counts(git_repo: Path) -> None:
    base = branch(git_repo)
    commit_file(git_repo, "PROGRESS.md", "# Mine\n", attempt_message("T01", 1))
    commit_file(git_repo, "hello.py", "x = 1\n", attempt_message("T01", 2))
    assert edited_notes(ctx(git_repo, base)) == ["PROGRESS.md"]


def test_main_changing_a_notes_file_meanwhile_does_not_count(git_repo: Path) -> None:
    base = branch(git_repo)
    commit_file(git_repo, "hello.py", "x = 1\n", attempt_message("T01", 1))
    run_git(git_repo, "checkout", "--quiet", "main")
    main = commit_file(git_repo, "PROGRESS.md", "# Progress\n\nMore.\n", "main moved")
    run_git(git_repo, "checkout", "--quiet", "feat")
    run_git(git_repo, "merge", "--quiet", "--no-edit", "-m", "spool: merge main into feat", "main")
    commit_file(git_repo, "bye.py", "y = 1\n", attempt_message("T01", 2))
    assert edited_notes(ctx(git_repo, base)) == []
    assert edited_notes(ctx(git_repo, main)) == []


def test_a_resolved_conflict_merge_by_an_attempt_does_not_count_main(git_repo: Path) -> None:
    branch(git_repo)
    commit_file(git_repo, "hello.py", "x = 1\n", attempt_message("T01", 1))
    run_git(git_repo, "checkout", "--quiet", "main")
    main = commit_file(git_repo, "PROGRESS.md", "# Progress\n\nMore.\n", "main moved")
    run_git(git_repo, "checkout", "--quiet", "feat")
    run_git(git_repo, "merge", "--quiet", "--no-edit", "-m", attempt_message("T01", 2), "main")
    # The integrator sets the base to the main it merged in (decision 394).
    assert edited_notes(ctx(git_repo, main)) == []


def test_spoolhqs_own_squash_on_a_pull_request_branch_does_not_count(git_repo: Path) -> None:
    base = branch(git_repo)
    commit_file(git_repo, "PROGRESS.md", "# Progress\n\n### T01\n", "T01: Say hello")
    commit_file(git_repo, "hello.py", "x = 2\n", attempt_message("T01", 2))
    assert edited_notes(ctx(git_repo, base)) == []
    commit_file(git_repo, "PROGRESS.md", "# Mine\n", attempt_message("T01", 3))
    assert edited_notes(ctx(git_repo, base)) == ["PROGRESS.md"]


def test_moving_a_notes_file_away_counts(git_repo: Path) -> None:
    base = branch(git_repo)
    run_git(git_repo, "mv", "PROGRESS.md", "old.md")
    run_git(git_repo, "commit", "--quiet", "--no-verify", "-m", attempt_message("T01", 1))
    assert edited_notes(ctx(git_repo, base)) == ["PROGRESS.md"]
