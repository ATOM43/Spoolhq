"""services/git: the runner, branch names and the main-repository checks."""

import subprocess
from pathlib import Path

import pytest

from spoolhq.services.git import (
    DirtyRepoError,
    GitError,
    GitResult,
    MissingBranchError,
    OperationInProgressError,
    branch_name,
    check_git_version,
    default_branch_sha,
    ensure_clean,
    ensure_no_operation_in_progress,
    runner,
    slugify,
)
from spoolhq.services.git.repo import status_entries
from tests.conftest import commit_file, run_git

# Runner -------------------------------------------------------------------------------


def test_git_error_names_the_subcommand_and_exit_code(wt_repo: Path) -> None:
    result = runner.run_git(["worktree", "remove", "no-such-worktree"], wt_repo)
    assert result.returncode == 128
    with pytest.raises(GitError) as excinfo:
        result.check()
    error = excinfo.value
    assert str(error).startswith("git worktree remove failed (exit 128): fatal: ")
    assert error.command == ("worktree", "remove", "no-such-worktree")
    assert error.returncode == 128
    assert error.stderr.startswith("fatal: ")


def test_git_error_keeps_the_last_20_stderr_lines() -> None:
    stderr = "".join(f"line {n}\n" for n in range(1, 31))
    error = runner.command_error(GitResult(("commit", "-m", "x"), 1, "", stderr))
    assert error.stderr.splitlines() == [f"line {n}" for n in range(11, 31)]
    assert str(error).startswith("git commit failed (exit 1): line 11\n")


def test_error_without_stderr_has_no_colon() -> None:
    error = runner.command_error(GitResult(("status",), 2, "", "  \n"))
    assert str(error) == "git status failed (exit 2)"


def test_subcommand_skips_config_options() -> None:
    assert runner.subcommand(["-c", "user.useConfigOnly=true", "commit", "-m", "x"]) == "commit"
    assert runner.subcommand(["worktree", "add", "-b", "x"]) == "worktree add"
    assert runner.subcommand(["worktree", "--help"]) == "worktree"
    assert runner.subcommand([]) == ""


def test_run_git_sets_options_and_environment(
    wt_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen["command"] = command
        seen.update(kwargs)
        return subprocess.CompletedProcess(command, 0, "out", "err")

    monkeypatch.setenv("GIT_INDEX_FILE", "/elsewhere/index")
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    result = runner.run_git(["status", "--", "a b"], wt_repo, timeout=5)

    assert result == GitResult(("status", "--", "a b"), 0, "out", "err")
    command = seen["command"]
    assert isinstance(command, list)
    assert command[1:] == [
        "-c",
        "core.quotepath=off",
        "-c",
        "core.fsmonitor=false",
        "-c",
        f"core.hooksPath={runner.disabled_hooks_dir()}",
        "-c",
        "commit.gpgsign=false",
        "-c",
        "tag.gpgsign=false",
        "-c",
        "tag.forceSignAnnotated=false",
        "status",
        "--",
        "a b",
    ]
    assert seen["cwd"] == wt_repo
    assert seen["timeout"] == 5
    assert seen["encoding"] == "utf-8"
    assert seen["errors"] == "replace"
    assert seen["check"] is False
    assert seen["stdin"] is subprocess.DEVNULL
    assert "shell" not in seen
    env = seen["env"]
    assert isinstance(env, dict)
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["GIT_OPTIONAL_LOCKS"] == "0"
    assert env["LC_ALL"] == "C"
    assert env["LANGUAGE"] == "C"
    assert "GIT_INDEX_FILE" not in env


def test_hook_and_signing_overrides_come_before_the_subcommand(
    wt_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    runner.run_git(["commit", "-m", "x"], wt_repo)

    [command] = seen
    before_subcommand = command[: command.index("commit")]
    pairs = list(zip(before_subcommand[1::2], before_subcommand[2::2], strict=True))
    for option in (
        f"core.hooksPath={runner.disabled_hooks_dir()}",
        "commit.gpgsign=false",
        "tag.gpgsign=false",
        "tag.forceSignAnnotated=false",
    ):
        assert ("-c", option) in pairs


def test_disabled_hooks_dir_is_created_in_the_home_folder(home: Path) -> None:
    path = runner.disabled_hooks_dir()
    assert path == home / "hooks-disabled"
    assert path.is_dir()
    assert list(path.iterdir()) == []


def test_non_empty_hooks_dir_stops_git_from_starting(
    wt_repo: Path, home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hooks = runner.disabled_hooks_dir()
    (hooks / "post-commit").write_text("#!/bin/sh\n", encoding="utf-8")
    calls: list[object] = []
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: calls.append(a))

    with pytest.raises(GitError) as raised:
        runner.run_git(["status"], wt_repo)

    assert str(raised.value) == (
        f"{home / 'hooks-disabled'} must be empty; SpoolHQ uses it to disable git hooks"
    )
    assert calls == []


def test_missing_git_is_reported(wt_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "_git_path", None)
    monkeypatch.setattr(runner.shutil, "which", lambda name: None)
    with pytest.raises(GitError, match=r"^git not found on PATH$"):
        runner.run_git(["status"], wt_repo)


def test_git_is_looked_up_once(wt_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    real_which = runner.shutil.which

    def which(name: str) -> str | None:
        calls.append(name)
        return real_which(name)

    monkeypatch.setattr(runner, "_git_path", None)
    monkeypatch.setattr(runner.shutil, "which", which)
    runner.run_git(["status"], wt_repo)
    runner.run_git(["status"], wt_repo)
    assert calls == ["git"]


def test_timeout_raises_git_error(wt_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def slow(command: list[str], **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(command, 0.5)

    monkeypatch.setattr(runner.subprocess, "run", slow)
    with pytest.raises(GitError, match=r"^git fetch did not finish within 0.5 s$"):
        runner.run_git(["fetch"], wt_repo, timeout=0.5)


def test_missing_folder_raises_git_error(tmp_path: Path) -> None:
    with pytest.raises(GitError, match="cannot run git status in"):
        runner.run_git(["status"], tmp_path / "gone")


def fake_version(monkeypatch: pytest.MonkeyPatch, output: str) -> None:
    def run_git(args: list[str], cwd: Path, **kwargs: object) -> GitResult:
        assert args == ["--version"]
        return GitResult(tuple(args), 0, output, "")

    monkeypatch.setattr(runner, "run_git", run_git)


def test_old_git_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_version(monkeypatch, "git version 2.34.1\n")
    with pytest.raises(GitError) as excinfo:
        check_git_version()
    assert str(excinfo.value) == "git 2.36 or newer is required (found 2.34.1)"


@pytest.mark.parametrize(
    ("output", "version"),
    [
        ("git version 2.36.0\n", (2, 36, 0)),
        ("git version 2.39.3 (Apple Git-145)\n", (2, 39, 3)),
        ("git version 2.45.1.windows.1\n", (2, 45, 1)),
        ("git version 3.0\n", (3, 0, 0)),
    ],
)
def test_supported_git_versions(
    monkeypatch: pytest.MonkeyPatch, output: str, version: tuple[int, int, int]
) -> None:
    fake_version(monkeypatch, output)
    assert check_git_version() == version


def test_unreadable_git_version(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_version(monkeypatch, "hub version 1\n")
    with pytest.raises(GitError, match="cannot read the git version"):
        check_git_version()


def test_installed_git_is_new_enough() -> None:
    assert check_git_version()[:2] >= runner.MIN_GIT_VERSION


# Branch names -------------------------------------------------------------------------


SLUGS = [
    ('Fix "quoted" thing; rm -rf /', "fix-quoted-thing-rm-rf"),
    ("Café über ünïcode", "cafe-uber-unicode"),
    (";;;\"\"''", "ticket"),
    ("a" * 100, "a" * 40),
    ("a" * 39 + "-b", "a" * 39),
    ("$(touch pwned) && `id`", "touch-pwned-id"),
    ("", "ticket"),
    ("  Already-a-slug  ", "already-a-slug"),
    ("ﬁ Ⅳ ① ｆｕｌｌ", "fi-iv-1-full"),
    ("..lock/@{-1}~^:?*[\\", "lock-1"),
]


@pytest.mark.parametrize(("title", "slug"), SLUGS)
def test_slugify(title: str, slug: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert slugify(title) == slug
    name = branch_name("T04", title)
    assert name == f"feat/T04-{slug}"
    assert runner.run_git(["check-ref-format", "--branch", name], tmp_path).returncode == 0
    assert not (tmp_path / "pwned").exists()


def test_quotes_and_semicolons_make_a_valid_branch(wt_repo: Path, tmp_path: Path) -> None:
    assert branch_name("T04", 'Fix "quoted" thing; rm -rf /', cwd=wt_repo) == (
        "feat/T04-fix-quoted-thing-rm-rf"
    )
    branch_name("T04", "$(touch pwned) && `id`", cwd=wt_repo)
    assert list(tmp_path.rglob("pwned")) == []


@pytest.mark.parametrize("ticket_id", ["T4", "T1234", "t04", "../T04", "T04/x", "T04\n"])
def test_branch_name_refuses_bad_ticket_ids(ticket_id: str) -> None:
    with pytest.raises(ValueError, match="invalid ticket id"):
        branch_name(ticket_id, "title")


def test_branch_name_raises_if_git_refuses_it(monkeypatch: pytest.MonkeyPatch) -> None:
    from spoolhq.services.git import naming

    monkeypatch.setattr(naming, "slugify", lambda title: "bad..name")
    with pytest.raises(GitError, match="bug: 'feat/T04-bad..name' is not a valid branch name"):
        naming.branch_name("T04", "anything")


# Repository checks --------------------------------------------------------------------


def test_clean_repo_passes(wt_repo: Path) -> None:
    ensure_clean(wt_repo)
    ensure_no_operation_in_progress(wt_repo)


def test_dirty_repo_lists_tracked_and_untracked_changes(wt_repo: Path) -> None:
    (wt_repo / "README.md").write_text("changed\n", encoding="utf-8")
    (wt_repo / "notes.txt").write_text("todo\n", encoding="utf-8")
    with pytest.raises(DirtyRepoError) as excinfo:
        ensure_clean(wt_repo)
    assert str(excinfo.value) == (
        f"repo {wt_repo} has uncommitted changes; commit or stash them first:\n"
        "   M README.md\n"
        "  ?? notes.txt"
    )


def test_staged_changes_and_renames_are_listed(wt_repo: Path) -> None:
    run_git(wt_repo, "mv", "README.md", "DOC.md")
    assert status_entries(wt_repo) == ["R  README.md -> DOC.md"]
    with pytest.raises(DirtyRepoError, match="R  README.md -> DOC.md"):
        ensure_clean(wt_repo)


def test_dirty_message_lists_20_entries(wt_repo: Path) -> None:
    for n in range(25):
        (wt_repo / f"file{n:02d}.txt").write_text("x\n", encoding="utf-8")
    with pytest.raises(DirtyRepoError) as excinfo:
        ensure_clean(wt_repo)
    lines = str(excinfo.value).splitlines()
    assert len(lines) == 22
    assert lines[1:21] == [f"  ?? file{n:02d}.txt" for n in range(20)]
    assert lines[-1] == "  … and 5 more"


def test_ignored_files_do_not_count(wt_repo: Path) -> None:
    commit_file(wt_repo, ".gitignore", "*.log\nbuild/\n", "ignore logs")
    (wt_repo / "debug.log").write_text("x\n", encoding="utf-8")
    (wt_repo / "build").mkdir()
    (wt_repo / "build" / "out.bin").write_text("x\n", encoding="utf-8")
    ensure_clean(wt_repo)


def test_paths_with_spaces_and_unicode_are_listed_as_is(wt_repo: Path) -> None:
    (wt_repo / "my notés.txt").write_text("x\n", encoding="utf-8")
    assert status_entries(wt_repo) == ["?? my notés.txt"]


def start_conflicting_merge(repo: Path) -> None:
    run_git(repo, "switch", "--quiet", "-c", "other")
    commit_file(repo, "README.md", "other\n", "other change")
    run_git(repo, "switch", "--quiet", "main")
    commit_file(repo, "README.md", "main\n", "main change")
    result = subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [runner.git_executable(), "-C", str(repo), "merge", "other"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr


def test_merge_in_progress_is_refused(wt_repo: Path) -> None:
    start_conflicting_merge(wt_repo)
    with pytest.raises(OperationInProgressError) as excinfo:
        ensure_no_operation_in_progress(wt_repo)
    assert str(excinfo.value) == (
        f"repo {wt_repo}: a merge is in progress; finish or abort it first"
    )


@pytest.mark.parametrize(
    ("git_path", "operation"),
    [
        ("rebase-merge", "rebase"),
        ("rebase-apply", "rebase"),
        ("CHERRY_PICK_HEAD", "cherry-pick"),
        ("REVERT_HEAD", "revert"),
    ],
)
def test_other_operations_are_named(wt_repo: Path, git_path: str, operation: str) -> None:
    target = wt_repo / ".git" / git_path
    if git_path.startswith("rebase"):
        target.mkdir()
    else:
        target.write_text(run_git(wt_repo, "rev-parse", "HEAD"), encoding="utf-8")
    with pytest.raises(OperationInProgressError, match=f": a {operation} is in progress;"):
        ensure_no_operation_in_progress(wt_repo)


def test_default_branch_sha(wt_repo: Path) -> None:
    assert default_branch_sha(wt_repo, "main") == run_git(wt_repo, "rev-parse", "main").strip()
    with pytest.raises(MissingBranchError) as excinfo:
        default_branch_sha(wt_repo, "trunk")
    assert str(excinfo.value) == f"default branch 'trunk' not found in {wt_repo}"


def test_default_branch_sha_outside_a_repo(tmp_path: Path) -> None:
    folder = tmp_path / "not-a-repo"
    folder.mkdir()
    with pytest.raises(GitError, match=r"git rev-parse failed \(exit 128\)"):
        default_branch_sha(folder, "main")
