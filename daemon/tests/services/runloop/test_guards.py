"""The guards' git diffs: the notes guard (only the attempts' own changes to the notes
files count) and the files the file-size gate checks."""

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from spoolhq.services.runloop.guards import attempt_message, changed_files, edited_notes
from spoolhq.services.runloop.model import RunContext
from tests.conftest import commit_file, run_git

# CI runners have no git config, so the commits need an identity from the environment.
pytestmark = pytest.mark.usefixtures("git_identity")


def ctx(repo: Path, base: str) -> RunContext:
    worktree = SimpleNamespace(path=repo, base_sha=base)
    project = SimpleNamespace(default_branch="main")
    return cast(RunContext, SimpleNamespace(worktree=worktree, ticket_id="T01", project=project))


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


def test_changed_files_come_with_their_content_before_the_ticket(git_repo: Path) -> None:
    branch(git_repo)
    commit_file(git_repo, "old.py", "a\n", "main file")
    base = commit_file(git_repo, "keep.txt", "k\n", "main file")
    run_git(git_repo, "branch", "-f", "main", "HEAD")
    commit_file(git_repo, "new.py", "n\n", attempt_message("T01", 1))
    commit_file(git_repo, "old.py", "a\nb\n", attempt_message("T01", 1))
    run_git(git_repo, "mv", "keep.txt", "moved.txt")
    run_git(git_repo, "commit", "--quiet", "--no-verify", "-m", attempt_message("T01", 2))
    assert sorted(changed_files(ctx(git_repo, base))) == [
        ("moved.txt", b"k\n"),
        ("new.py", None),
        ("old.py", b"a\n"),
    ]


def test_main_merged_into_the_branch_is_not_the_tickets_change(git_repo: Path) -> None:
    base = branch(git_repo)
    commit_file(git_repo, "mine.py", "x\n", attempt_message("T01", 1))
    run_git(git_repo, "checkout", "--quiet", "main")
    commit_file(git_repo, "theirs.py", "y\n", "main moved")
    run_git(git_repo, "checkout", "--quiet", "feat")
    run_git(git_repo, "merge", "--quiet", "--no-edit", "-m", "spool: merge main into feat", "main")
    assert changed_files(ctx(git_repo, base)) == [("mine.py", None)]
