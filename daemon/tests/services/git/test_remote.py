"""services/git/remote.py: fetch, compare, push, tags and branch deletion, against a
local bare repository standing in for GitHub."""

from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.git import (
    GitError,
    PushResult,
    delete_branch,
    fetch,
    github_repo,
    push,
    push_tag,
    remote_ref,
    runner,
    unpushed,
)
from tests.conftest import (
    GITHUB_URL,
    commit_file,
    make_github_remote,
    push_elsewhere,
    run_git,
    set_identity,
    write_hook,
)


def git(repo: Path, *args: str) -> str:
    return run_git(repo, *args).strip()


@pytest.fixture
def bare(git_repo: Path, tmp_path: Path, isolated_git: None) -> Path:
    set_identity(git_repo)
    return make_github_remote(git_repo, tmp_path / "remote.git")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/acme/demo", "acme/demo"),
        ("https://github.com/acme/demo.git", "acme/demo"),
        ("git@github.com:a-b/x.y_z.git", "a-b/x.y_z"),
    ],
)
def test_github_repo(url: str, expected: str) -> None:
    assert github_repo(url) == expected


@pytest.mark.parametrize("url", ["https://gitlab.com/a/b", "git@github.com:a/b", "../x.git"])
def test_github_repo_refuses_other_urls(url: str) -> None:
    with pytest.raises(ValueError, match="not a GitHub URL"):
        github_repo(url)


def test_fetch_stores_the_branch_under_spoolhq_refs(git_repo: Path, bare: Path) -> None:
    theirs = push_elsewhere(bare, bare.parent / "mate", "b.txt", "theirs")
    assert fetch(git_repo, GITHUB_URL, "main") == theirs
    assert git(git_repo, "rev-parse", remote_ref("main")) == theirs
    assert git(git_repo, "remote") == ""  # no remote was added
    assert git(git_repo, "rev-parse", "main") != theirs  # local main untouched


def test_unpushed_lists_local_commits(git_repo: Path, bare: Path) -> None:
    fetch(git_repo, GITHUB_URL, "main")
    assert unpushed(git_repo, "main") == []
    sha = commit_file(git_repo, "a.txt", "a\n", "mine, not pushed")
    assert unpushed(git_repo, "main") == [f"{sha[:7]} mine, not pushed"]


def test_push_a_commit_then_a_tag(git_repo: Path, bare: Path) -> None:
    sha = commit_file(git_repo, "a.txt", "a\n", "one")
    assert push(git_repo, GITHUB_URL, sha, "refs/heads/main") is PushResult.PUSHED
    assert git(bare, "rev-parse", "main") == sha
    git(git_repo, "tag", "ticket/T01", sha)
    push_tag(git_repo, GITHUB_URL, "ticket/T01")
    assert git(bare, "rev-parse", "refs/tags/ticket/T01") == sha


def test_a_push_behind_the_remote_is_moved_not_forced(git_repo: Path, bare: Path) -> None:
    theirs = push_elsewhere(bare, bare.parent / "mate", "b.txt", "theirs")
    mine = commit_file(git_repo, "a.txt", "a\n", "mine")
    assert push(git_repo, GITHUB_URL, mine, "refs/heads/main") is PushResult.MOVED
    assert git(bare, "rev-parse", "main") == theirs


def test_a_refused_push_raises_with_the_hook_output(git_repo: Path, bare: Path) -> None:
    write_hook(bare, "pre-receive", 'echo "policy: pushes to main are closed" >&2\nexit 1')
    sha = commit_file(git_repo, "a.txt", "a\n", "one")
    with pytest.raises(GitError) as caught:
        push(git_repo, GITHUB_URL, sha, "refs/heads/main")
    message = str(caught.value)
    assert "policy: pushes to main are closed" in message
    assert "pre-receive hook declined" in message


def test_delete_branch(git_repo: Path, bare: Path) -> None:
    sha = commit_file(git_repo, "a.txt", "a\n", "one")
    push(git_repo, GITHUB_URL, sha, "refs/heads/spoolhq/T01-x")
    delete_branch(git_repo, GITHUB_URL, "spoolhq/T01-x")
    assert run_git(bare, "branch", "--list", "spoolhq/T01-x").strip() == ""


def test_fetch_of_a_missing_branch_fails(git_repo: Path, bare: Path) -> None:
    with pytest.raises(GitError, match="git fetch failed"):
        fetch(git_repo, GITHUB_URL, "nope")


def _ssh_commands(monkeypatch: pytest.MonkeyPatch) -> list[str | None]:
    """Record the ``GIT_SSH_COMMAND`` each git call gets."""
    seen: list[str | None] = []
    real = runner.subprocess.run

    def spy(command: list[str], **kwargs: Any) -> Any:
        seen.append(kwargs["env"].get("GIT_SSH_COMMAND"))
        return real(command, **kwargs)

    monkeypatch.setattr(runner.subprocess, "run", spy)
    return seen


@pytest.mark.parametrize("action", ["fetch", "push", "delete"])
def test_remote_calls_run_ssh_in_batch_mode(
    git_repo: Path, bare: Path, monkeypatch: pytest.MonkeyPatch, action: str
) -> None:
    monkeypatch.delenv("GIT_SSH_COMMAND", raising=False)
    monkeypatch.delenv("GIT_SSH", raising=False)
    sha = commit_file(git_repo, "a.txt", "a\n", "one")
    push(git_repo, GITHUB_URL, sha, "refs/heads/x")
    seen = _ssh_commands(monkeypatch)
    if action == "fetch":
        fetch(git_repo, GITHUB_URL, "main")
    elif action == "push":
        push(git_repo, GITHUB_URL, sha, "refs/heads/main")
    else:
        delete_branch(git_repo, GITHUB_URL, "x")
    assert runner.SSH_BATCH_COMMAND in seen


def test_a_users_own_ssh_command_is_kept_with_one_warning(
    git_repo: Path, bare: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(runner, "_ssh_warned", False)
    monkeypatch.setenv("GIT_SSH_COMMAND", "ssh -i mykey")
    seen = _ssh_commands(monkeypatch)
    fetch(git_repo, GITHUB_URL, "main")
    fetch(git_repo, GITHUB_URL, "main")
    assert runner.SSH_BATCH_COMMAND not in seen
    assert "ssh -i mykey" in seen
    warnings = [r for r in caplog.records if "passphrase prompt could hang" in r.message]
    assert len(warnings) == 1


def test_a_users_core_ssh_command_is_kept(
    git_repo: Path, bare: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GIT_SSH_COMMAND", raising=False)
    monkeypatch.delenv("GIT_SSH", raising=False)
    run_git(git_repo, "config", "core.sshCommand", "ssh -i mykey")
    seen = _ssh_commands(monkeypatch)
    fetch(git_repo, GITHUB_URL, "main")
    assert runner.SSH_BATCH_COMMAND not in seen
