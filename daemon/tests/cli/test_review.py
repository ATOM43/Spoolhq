"""`spool review`."""

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from spoolhq.cli import app, review
from spoolhq.services.agents import FakeRunner
from tests.conftest import REVIEW_FIXTURES, commit_file, run_git, set_identity

runner = CliRunner()


@pytest.fixture
def repo(workspace: Path, git_repo: Path, isolated_git: None) -> Path:
    """The demo project with ticket T07 and parse_slug committed on a branch."""
    tickets = workspace / "tickets"
    tickets.mkdir(exist_ok=True)
    shutil.copyfile(REVIEW_FIXTURES / "T07-parse-slug.md", tickets / "T07-parse-slug.md")
    set_identity(git_repo)
    run_git(git_repo, "checkout", "--quiet", "-b", "feat/T07-parse-slug")
    commit_file(git_repo, "slugs.py", "def parse_slug(text):\n    return text\n", "T07")
    return git_repo


def fake(monkeypatch: pytest.MonkeyPatch, *names: str) -> FakeRunner:
    runner_ = FakeRunner([REVIEW_FIXTURES / f"{name}.jsonl" for name in names])
    monkeypatch.setattr(review, "make_runner", lambda: runner_)
    return runner_


def test_changes_requested_exits_1(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = fake(monkeypatch, "changes_requested")

    result = runner.invoke(app, ["review", "demo", "T07", "--path", str(repo)])

    assert result.exit_code == 1, result.stderr
    assert result.stdout.splitlines() == [
        "✓ 1. `parse_slug` exists in `slugs.py`",
        "✗ 2. A test covers parse_slug — no test for parse_slug",
        "✓ 3. `just test` passes",
        "verdict: changes_requested",
        "parse_slug has no test.",
    ]
    assert "not yet checked by the gates: 3. `just test` passes" in result.stderr
    [(prompt, policy)] = agent.calls
    assert "+def parse_slug(text):" in prompt
    assert policy.read_only
    assert policy.worktree == repo.resolve()


def test_approve_exits_0_and_defaults_to_the_repo(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake(monkeypatch, "approve")
    result = runner.invoke(app, ["review", "demo", "T07", "--base", "main"])
    assert result.exit_code == 0, result.stderr
    assert result.stdout.splitlines()[-2] == "verdict: approve"


def test_unfinished_run_exits_2(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake(monkeypatch, "usage_limited")
    result = runner.invoke(app, ["review", "demo", "T07", "--path", str(repo)])
    assert result.exit_code == 2
    assert "review did not finish: usage_limited" in result.stderr


def test_dirty_repo_is_refused(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = fake(monkeypatch, "approve")
    (repo / "notes.txt").write_text("not committed\n", encoding="utf-8")

    result = runner.invoke(app, ["review", "demo", "T07", "--path", str(repo)])

    assert result.exit_code == 1
    assert "has uncommitted changes; commit or stash them first" in result.stderr
    assert agent.calls == []


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["review", "demo", "T99"], "no ticket T99"),
        (["review", "nope", "T07"], "error:"),
        (["review", "demo", "T07", "--base", "no-such-branch"], "git diff"),
    ],
)
def test_errors(repo: Path, monkeypatch: pytest.MonkeyPatch, args: list[str], message: str) -> None:
    fake(monkeypatch, "approve")
    result = runner.invoke(app, args)
    assert result.exit_code == 1
    assert message in result.stderr


def test_not_a_repository(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake(monkeypatch, "approve")
    folder = tmp_path / "plain"
    folder.mkdir()
    result = runner.invoke(app, ["review", "demo", "T07", "--path", str(folder)])
    assert result.exit_code == 1
    assert "not a git repository" in result.stderr


def test_ticket_without_done_when_items(
    repo: Path, workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake(monkeypatch, "approve")
    ticket = workspace / "tickets" / "T07-parse-slug.md"
    text = ticket.read_text(encoding="utf-8")
    ticket.write_text(text.split("## Done when")[0], encoding="utf-8")
    result = runner.invoke(app, ["review", "demo", "T07", "--path", str(repo)])
    assert result.exit_code == 1
    assert "T07 has no 'Done when' items" in result.stderr
