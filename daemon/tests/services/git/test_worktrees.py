"""services/git: creating, committing in, tearing down and listing worktrees."""

import logging
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from spoolhq.services.git import (
    BranchConflictError,
    DirtyRepoError,
    GitError,
    IdentityError,
    MissingBranchError,
    OperationInProgressError,
    Worktree,
    WorktreeExistsError,
    WorktreeInfo,
    WorktreeManager,
    WorktreeState,
)
from spoolhq.services.git import worktrees as worktrees_module
from spoolhq.services.git.runner import git_executable
from spoolhq.services.git.worktrees import parse_worktree_list, remove_path
from tests.conftest import commit_file, run_git

TITLE = 'Say "hi"; echo bad'
BRANCH = "feat/T04-say-hi-echo-bad"


def sha(repo: Path, ref: str) -> str:
    return run_git(repo, "rev-parse", ref).strip()


def branches(repo: Path) -> list[str]:
    return run_git(repo, "branch", "--list", "--format=%(refname:short)").split()


def marker(repo: Path, branch: str) -> str | None:
    result = subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [git_executable(), "-C", str(repo), "config", "--get", f"branch.{branch}.spoolhq"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def registered_paths(repo: Path) -> list[Path]:
    output = run_git(repo, "worktree", "list", "--porcelain", "-z")
    return [Path(os.path.realpath(entry.path)) for entry in parse_worktree_list(output)]


def real(path: Path) -> Path:
    return Path(os.path.realpath(path))


# Create -------------------------------------------------------------------------------


def test_create_makes_a_marked_worktree_on_the_ticket_branch(
    manager: WorktreeManager, wt_repo: Path, wt_root: Path
) -> None:
    wt = manager.create("T04", TITLE, 17)

    assert wt == Worktree(
        ticket_id="T04",
        branch=BRANCH,
        path=wt_root / "demo" / "T04",
        base_sha=sha(wt_repo, "main"),
        run_id="17",
    )
    assert wt.path.is_dir()
    assert (wt.path / "README.md").read_text(encoding="utf-8") == "# demo\n"
    assert run_git(wt.path, "branch", "--show-current").strip() == BRANCH
    assert BRANCH in branches(wt_repo)
    assert marker(wt_repo, BRANCH) == "17"
    assert real(wt.path) in registered_paths(wt_repo)
    # The main repository stays on main and clean.
    assert run_git(wt_repo, "branch", "--show-current").strip() == "main"
    assert run_git(wt_repo, "status", "--porcelain") == ""


def test_dirty_repo_creates_nothing(manager: WorktreeManager, wt_repo: Path, wt_root: Path) -> None:
    (wt_repo / "README.md").write_text("changed\n", encoding="utf-8")
    (wt_repo / "notes.txt").write_text("todo\n", encoding="utf-8")
    with pytest.raises(DirtyRepoError) as excinfo:
        manager.create("T04", TITLE, 1)
    assert " M README.md" in str(excinfo.value)
    assert "?? notes.txt" in str(excinfo.value)
    assert not (wt_root / "demo" / "T04").exists()
    assert branches(wt_repo) == ["main"]


def test_merge_in_progress_creates_nothing(manager: WorktreeManager, wt_repo: Path) -> None:
    run_git(wt_repo, "switch", "--quiet", "-c", "other")
    commit_file(wt_repo, "README.md", "other\n", "other change")
    run_git(wt_repo, "switch", "--quiet", "main")
    commit_file(wt_repo, "README.md", "main\n", "main change")
    subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [git_executable(), "-C", str(wt_repo), "merge", "other"], capture_output=True, check=False
    )
    with pytest.raises(OperationInProgressError, match="a merge is in progress"):
        manager.create("T04", TITLE, 1)
    assert branches(wt_repo) == ["main", "other"]


def test_missing_default_branch(wt_repo: Path, wt_root: Path) -> None:
    trunk = WorktreeManager(wt_repo, "demo", "trunk", wt_root)
    with pytest.raises(MissingBranchError) as excinfo:
        trunk.create("T04", TITLE, 1)
    assert str(excinfo.value) == f"default branch 'trunk' not found in {wt_repo}"
    assert not (wt_root / "demo" / "T04").exists()
    assert branches(wt_repo) == ["main"]


def test_marked_stale_branch_is_recreated_from_main(
    manager: WorktreeManager, wt_repo: Path, caplog: pytest.LogCaptureFixture
) -> None:
    old = manager.create("T04", TITLE, 1)
    (old.path / "work.txt").write_text("old work\n", encoding="utf-8")
    manager.commit_all(old, "T04: old work")
    manager.teardown(old, delete_branch=False)
    assert BRANCH in branches(wt_repo)
    new_main = commit_file(wt_repo, "CHANGELOG.md", "x\n", "main moves on")

    caplog.set_level(logging.INFO)
    wt = manager.create("T04", TITLE, 2)

    assert wt.base_sha == new_main
    assert sha(wt_repo, BRANCH) == new_main
    assert not (wt.path / "work.txt").exists()
    assert marker(wt_repo, BRANCH) == "2"
    assert f"recreating stale SpoolHQ branch {BRANCH}" in caplog.messages


def test_unmarked_branch_is_left_alone(manager: WorktreeManager, wt_repo: Path) -> None:
    run_git(wt_repo, "switch", "--quiet", "-c", BRANCH)
    theirs = commit_file(wt_repo, "theirs.txt", "mine\n", "someone else's work")
    run_git(wt_repo, "switch", "--quiet", "main")

    with pytest.raises(BranchConflictError) as excinfo:
        manager.create("T04", TITLE, 1)

    assert str(excinfo.value) == (
        f"branch {BRANCH} exists and was not created by SpoolHQ; rename or delete it"
    )
    assert sha(wt_repo, BRANCH) == theirs
    assert not manager.path_for("T04").exists()


def test_marked_branch_checked_out_elsewhere_is_refused(
    manager: WorktreeManager, wt_repo: Path, tmp_path: Path
) -> None:
    manager.teardown(manager.create("T04", TITLE, 1), delete_branch=False)
    elsewhere = tmp_path / "elsewhere"
    run_git(wt_repo, "worktree", "add", "--quiet", str(elsewhere), BRANCH)
    with pytest.raises(BranchConflictError, match=f"branch {BRANCH} is checked out at"):
        manager.create("T04", TITLE, 2)
    assert marker(wt_repo, BRANCH) == "1"


def test_second_create_raises(manager: WorktreeManager) -> None:
    wt = manager.create("T04", TITLE, 1)
    with pytest.raises(WorktreeExistsError) as excinfo:
        manager.create("T04", "another title", 2)
    assert str(excinfo.value) == (
        f"T04 already has a worktree at {wt.path}; resume it or remove it first"
    )


def test_existing_folder_counts_as_a_worktree(manager: WorktreeManager, wt_repo: Path) -> None:
    manager.path_for("T04").mkdir(parents=True)
    with pytest.raises(WorktreeExistsError):
        manager.create("T04", TITLE, 1)
    assert branches(wt_repo) == ["main"]


def test_failure_after_worktree_add_tears_down(
    manager: WorktreeManager, wt_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_git = manager._git

    def failing_config(*args: str, cwd: Path | None = None) -> object:
        if args[:2] == ("config", "--local") and not args[2].startswith("--"):
            raise GitError("git config failed (exit 1): simulated")
        return real_git(*args, cwd=cwd)

    monkeypatch.setattr(manager, "_git", failing_config)
    with pytest.raises(GitError, match="simulated"):
        manager.create("T04", TITLE, 1)
    monkeypatch.undo()

    assert not manager.path_for("T04").exists()
    assert branches(wt_repo) == ["main"]
    assert registered_paths(wt_repo) == [real(wt_repo)]


def test_failed_worktree_add_leaves_nothing(
    manager: WorktreeManager, wt_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_git = manager._git

    def bad_base(*args: str, cwd: Path | None = None) -> object:
        if args[:2] == ("worktree", "add"):
            args = (*args[:-1], "0" * 40)
        return real_git(*args, cwd=cwd)

    monkeypatch.setattr(manager, "_git", bad_base)
    with pytest.raises(GitError, match=r"^git worktree add failed \(exit 128\)"):
        manager.create("T04", TITLE, 1)
    monkeypatch.undo()
    assert not manager.path_for("T04").exists()
    assert branches(wt_repo) == ["main"]


def test_create_validates_its_arguments(manager: WorktreeManager, wt_root: Path) -> None:
    with pytest.raises(ValueError, match="invalid ticket id"):
        manager.create("../T04", TITLE, 1)
    with pytest.raises(ValueError, match="run_id must not be empty"):
        manager.create("T04", TITLE, " ")
    with pytest.raises(ValueError, match="invalid project name"):
        WorktreeManager(manager.repo, "../demo", "main", wt_root)
    assert not wt_root.exists()


# Resume -------------------------------------------------------------------------------


def test_resume_returns_the_worktree(manager: WorktreeManager, wt_repo: Path) -> None:
    wt = manager.create("T04", TITLE, 5)
    (wt.path / "a.txt").write_text("a\n", encoding="utf-8")
    manager.commit_all(wt, "T04: a")
    commit_file(wt_repo, "other.txt", "x\n", "main moves on")

    assert manager.resume("T04") == wt
    assert manager.resume("T05") is None


def test_resume_needs_the_folder_and_the_marker(manager: WorktreeManager, wt_repo: Path) -> None:
    wt = manager.create("T04", TITLE, 5)
    run_git(wt_repo, "config", "--unset", f"branch.{BRANCH}.spoolhq")
    assert manager.resume("T04") is None
    run_git(wt_repo, "config", f"branch.{BRANCH}.spoolhq", "5")
    remove_path(wt.path)
    assert manager.resume("T04") is None


# Commit -------------------------------------------------------------------------------


def test_commit_all_commits_on_top_of_the_base(manager: WorktreeManager) -> None:
    wt = manager.create("T04", TITLE, 1)
    (wt.path / "new.txt").write_text("new\n", encoding="utf-8")
    (wt.path / "README.md").write_text("# changed\n", encoding="utf-8")

    commit = manager.commit_all(wt, "T04: test")

    assert commit is not None
    assert commit == sha(wt.path, "HEAD")
    assert sha(wt.path, f"{commit}^") == wt.base_sha
    assert run_git(wt.path, "status", "--porcelain") == ""
    assert manager.commit_all(wt, "T04: nothing") is None
    assert sha(wt.path, "HEAD") == commit


def test_commit_skips_repo_hooks(manager: WorktreeManager, wt_repo: Path) -> None:
    hook = wt_repo / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(exist_ok=True)
    hook.write_text("#!/bin/sh\necho hook ran >&2\nexit 1\n", encoding="utf-8", newline="\n")
    hook.chmod(0o755)
    wt = manager.create("T04", TITLE, 1)
    (wt.path / "x.txt").write_text("x\n", encoding="utf-8")

    # The hook does block an ordinary commit.
    run_git(wt.path, "add", "-A")
    plain = subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [git_executable(), "-C", str(wt.path), "commit", "-m", "plain"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert plain.returncode != 0
    assert "hook ran" in plain.stderr

    assert manager.commit_all(wt, "T04: with hook") is not None


def test_commit_message_is_stored_verbatim(manager: WorktreeManager) -> None:
    wt = manager.create("T04", TITLE, 1)
    (wt.path / "x.txt").write_text("x\n", encoding="utf-8")
    message = 'T04: "; rm -rf ~ $(id) `id` -n'
    manager.commit_all(wt, message)
    assert run_git(wt.path, "log", "-1", "--format=%B").strip() == message


def test_commit_without_identity_is_refused(manager: WorktreeManager, wt_repo: Path) -> None:
    wt = manager.create("T04", TITLE, 1)
    run_git(wt_repo, "config", "--unset", "user.name")
    run_git(wt_repo, "config", "--unset", "user.email")
    (wt.path / "x.txt").write_text("x\n", encoding="utf-8")
    with pytest.raises(IdentityError) as excinfo:
        manager.commit_all(wt, "T04: x")
    assert str(excinfo.value) == (
        f"git user.name/user.email not set for {wt_repo}; set them with git config"
    )
    assert sha(wt.path, "HEAD") == wt.base_sha


def test_commit_refuses_an_empty_message(manager: WorktreeManager) -> None:
    wt = manager.create("T04", TITLE, 1)
    with pytest.raises(ValueError, match="must not be empty"):
        manager.commit_all(wt, "  ")


# Teardown -----------------------------------------------------------------------------


def test_teardown_removes_folder_branch_and_marker(manager: WorktreeManager, wt_repo: Path) -> None:
    wt = manager.create("T04", TITLE, 1)
    (wt.path / "x.txt").write_text("uncommitted\n", encoding="utf-8")

    manager.teardown(wt)

    assert not wt.path.exists()
    assert branches(wt_repo) == ["main"]
    assert marker(wt_repo, BRANCH) is None
    assert registered_paths(wt_repo) == [real(wt_repo)]
    manager.teardown(wt)
    manager.teardown("T04")


def test_teardown_by_ticket_id(manager: WorktreeManager, wt_repo: Path) -> None:
    manager.create("T04", TITLE, 1)
    manager.teardown("T04")
    assert not manager.path_for("T04").exists()
    assert branches(wt_repo) == ["main"]


def test_teardown_can_keep_the_branch(manager: WorktreeManager, wt_repo: Path) -> None:
    wt = manager.create("T04", TITLE, 1)
    manager.teardown(wt, delete_branch=False)
    assert not wt.path.exists()
    assert BRANCH in branches(wt_repo)
    assert marker(wt_repo, BRANCH) == "1"


def test_teardown_never_deletes_an_unmarked_branch(manager: WorktreeManager, wt_repo: Path) -> None:
    wt = manager.create("T04", TITLE, 1)
    run_git(wt_repo, "config", "--unset", f"branch.{BRANCH}.spoolhq")
    manager.teardown(wt)
    assert not wt.path.exists()
    assert BRANCH in branches(wt_repo)


def make_read_only(folder: Path) -> Path:
    """A read-only file in a read-only subfolder (Windows refuses the first, POSIX the second)."""
    sub = folder / "locked"
    sub.mkdir()
    target = sub / "read-only.txt"
    target.write_text("x\n", encoding="utf-8")
    target.chmod(stat.S_IREAD)
    sub.chmod(stat.S_IREAD | stat.S_IEXEC)
    return target


def test_teardown_removes_read_only_files(manager: WorktreeManager, wt_repo: Path) -> None:
    wt = manager.create("T04", TITLE, 1)
    make_read_only(wt.path)
    manager.teardown(wt)
    assert not wt.path.exists()
    assert branches(wt_repo) == ["main"]


def test_teardown_deletes_the_folder_when_git_cannot(
    manager: WorktreeManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    wt = manager.create("T04", TITLE, 1)
    make_read_only(wt.path)
    real_git = manager._git

    def no_remove(*args: str, cwd: Path | None = None) -> object:
        if args[:2] == ("worktree", "remove"):
            args = ("worktree", "remove", "--no-such-option")
        return real_git(*args, cwd=cwd)

    monkeypatch.setattr(manager, "_git", no_remove)
    manager.teardown(wt)
    assert not wt.path.exists()
    assert manager.list_worktrees() == []


def test_read_only_handler_retries_once(tmp_path: Path) -> None:
    target = tmp_path / "read-only.txt"
    target.write_text("x\n", encoding="utf-8")
    target.chmod(stat.S_IREAD)
    worktrees_module._clear_read_only_and_retry(os.remove, str(target), PermissionError())
    assert not target.exists()
    with pytest.raises(FileNotFoundError):
        worktrees_module._clear_read_only_and_retry(os.remove, str(target), PermissionError())


def test_remove_path_handles_files_and_symlinks(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("x\n", encoding="utf-8")
    link = tmp_path / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks need extra rights on this system")
    remove_path(link)
    assert not link.exists()
    assert (outside / "keep.txt").exists()

    stray = tmp_path / "stray.txt"
    stray.write_text("x\n", encoding="utf-8")
    stray.chmod(stat.S_IREAD)
    remove_path(stray)
    assert not stray.exists()
    remove_path(tmp_path / "missing")


# Session ------------------------------------------------------------------------------


def test_session_tears_down_after_an_exception(manager: WorktreeManager, wt_repo: Path) -> None:
    with pytest.raises(RuntimeError, match="agent crashed"):
        with manager.session("T04", TITLE, 1) as wt:
            assert wt.path.is_dir()
            (wt.path / "x.txt").write_text("x\n", encoding="utf-8")
            raise RuntimeError("agent crashed")
    assert not wt.path.exists()
    assert branches(wt_repo) == ["main"]


def test_session_tears_down_on_normal_exit(manager: WorktreeManager, wt_repo: Path) -> None:
    with manager.session("T04", TITLE, 1) as wt:
        (wt.path / "x.txt").write_text("x\n", encoding="utf-8")
        assert manager.commit_all(wt, "T04: x") is not None
    assert not wt.path.exists()
    assert branches(wt_repo) == ["main"]


def test_session_keep_leaves_the_worktree(manager: WorktreeManager, wt_repo: Path) -> None:
    with manager.session("T04", TITLE, 1) as wt:
        assert isinstance(wt, Worktree)
        wt.keep()
    assert wt.kept
    assert wt.path.is_dir()
    assert manager.resume("T04") == Worktree("T04", BRANCH, wt.path, wt.base_sha, "1")


def test_session_teardown_failure_keeps_the_original_error(
    manager: WorktreeManager, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def broken(*args: object, **kwargs: object) -> None:
        raise GitError("teardown broke")

    with pytest.raises(RuntimeError, match="original"):
        with manager.session("T04", TITLE, 1):
            monkeypatch.setattr(manager, "teardown", broken)
            raise RuntimeError("original")
    assert "cannot tear down the worktree" in caplog.messages


# Listing ------------------------------------------------------------------------------


def test_list_worktrees_reports_each_state(
    manager: WorktreeManager, wt_repo: Path, wt_root: Path, tmp_path: Path
) -> None:
    assert manager.list_worktrees() == []
    ok = manager.create("T04", TITLE, 1)
    gone = manager.create("T05", "gone", 2)
    remove_path(gone.path)
    (wt_root / "demo" / "T06").mkdir()
    (wt_root / "demo" / "notes").mkdir()
    run_git(wt_repo, "worktree", "add", "--quiet", "-b", "plain", str(wt_root / "demo" / "T07"))
    run_git(wt_repo, "worktree", "add", "--quiet", "-b", "out", str(tmp_path / "out" / "T08"))
    other = WorktreeManager(wt_repo, "other", "main", wt_root)
    other.create("T09", "other project", 3)

    infos = manager.list_worktrees()

    assert [(info.ticket_id, info.state) for info in infos] == [
        ("T04", WorktreeState.OK),
        ("T05", WorktreeState.MISSING_FOLDER),
        ("T06", WorktreeState.NOT_REGISTERED),
        ("T07", WorktreeState.NO_MARKER),
    ]
    assert infos[0] == WorktreeInfo("T04", ok.path, BRANCH, True, True, True)
    assert infos[2] == WorktreeInfo("T06", wt_root / "demo" / "T06", None, False, True, False)
    assert infos[3].branch == "plain"
    assert [info.ticket_id for info in other.list_worktrees()] == ["T09"]


def test_parse_worktree_list() -> None:
    output = (
        "worktree /repo\0HEAD aaa\0branch refs/heads/main\0\0"
        "worktree /wt/T04\0HEAD bbb\0detached\0locked\0\0"
        "worktree /bare\0bare\0\0"
        "worktree /wt/T05\0HEAD ccc\0branch refs/heads/feat/T05-x\0prunable gitdir file "
        "points to non-existent location\0\0"
    )
    entries = parse_worktree_list(output)
    assert [(str(e.path), e.branch) for e in entries] == [
        (str(Path("/repo")), "main"),
        (str(Path("/wt/T04")), None),
        (str(Path("/bare")), None),
        (str(Path("/wt/T05")), "feat/T05-x"),
    ]
    assert entries[1].detached and entries[1].locked
    assert entries[2].bare
    assert entries[3].prunable
    assert parse_worktree_list("") == []


@pytest.mark.skipif(sys.platform != "win32", reason="Windows paths compare case-insensitively")
def test_paths_compare_case_insensitively_on_windows(tmp_path: Path) -> None:
    assert worktrees_module.same_path(tmp_path, Path(str(tmp_path).upper()))
