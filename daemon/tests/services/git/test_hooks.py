"""services/git: SpoolHQ's git calls never run repository hooks and never sign."""

import re
import subprocess
import time
from pathlib import Path

import pytest

import spoolhq
from spoolhq.services.git import WorktreeManager
from spoolhq.services.git import run_git as spool_git
from spoolhq.services.git.runner import git_executable
from tests.conftest import run_git

TITLE = "Hooks"
HOOKS = ("post-checkout", "prepare-commit-msg", "post-commit", "pre-commit")


@pytest.fixture
def markers(tmp_path: Path) -> Path:
    """A folder outside every repository that the test hooks write into."""
    folder = tmp_path / "hook-markers"
    folder.mkdir()
    return folder


def fired(markers: Path) -> list[str]:
    return sorted(path.name for path in markers.iterdir())


def clear(markers: Path) -> None:
    for path in markers.iterdir():
        path.unlink()


def write_hook(folder: Path, name: str, markers: Path) -> Path:
    """A ``#!/bin/sh`` hook that records its own name in ``markers`` (absolute path)."""
    folder.mkdir(parents=True, exist_ok=True)
    hook = folder / name
    hook.write_text(
        f'#!/bin/sh\necho {name} > "{markers.as_posix()}/{name}"\nexit 0\n',
        encoding="utf-8",
        newline="\n",
    )
    hook.chmod(0o755)
    return hook


def plain_commit(repo: Path) -> None:
    """What a person's own ``git commit`` does: all hooks enabled, no SpoolHQ options."""
    subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [git_executable(), "-C", str(repo), "commit", "--quiet", "--allow-empty", "-m", "x"],
        capture_output=True,
        text=True,
        check=True,
    )


def require_hooks_fire(repo: Path, markers: Path) -> None:
    """Control: the hooks do run for a plain commit on this machine, or the test is moot."""
    plain_commit(repo)
    if not fired(markers):
        pytest.skip("git hooks do not run on this machine, so their absence proves nothing")
    clear(markers)


def commit_hooks(repo: Path, markers: Path) -> None:
    """Commit executable hooks in ``.githooks/`` and point ``core.hooksPath`` at it."""
    for name in HOOKS:
        write_hook(repo / ".githooks", name, markers)
    run_git(repo, "add", "--chmod=+x", "--", ".githooks")
    run_git(repo, "commit", "--quiet", "--no-verify", "-m", "add hooks")
    run_git(repo, "config", "core.hooksPath", ".githooks")


def test_tracked_hooks_folder_never_runs(
    manager: WorktreeManager, wt_repo: Path, markers: Path
) -> None:
    commit_hooks(wt_repo, markers)
    require_hooks_fire(wt_repo, markers)

    wt = manager.create("T04", TITLE, 1)
    (wt.path / "change.txt").write_text("change\n", encoding="utf-8")
    assert manager.commit_all(wt, "T04: change") is not None

    assert fired(markers) == []


def test_default_hooks_folder_never_runs(
    manager: WorktreeManager, wt_repo: Path, markers: Path
) -> None:
    for name in HOOKS:
        write_hook(wt_repo / ".git" / "hooks", name, markers)
    require_hooks_fire(wt_repo, markers)

    wt = manager.create("T04", TITLE, 1)
    (wt.path / "change.txt").write_text("change\n", encoding="utf-8")
    assert manager.commit_all(wt, "T04: change") is not None

    assert fired(markers) == []


def test_hook_written_by_the_agent_never_runs(
    manager: WorktreeManager, wt_repo: Path, markers: Path
) -> None:
    run_git(wt_repo, "config", "core.hooksPath", ".githooks")
    wt = manager.create("T04", TITLE, 1)
    # The agent adds a hook to the tracked hooks folder in its worktree, uncommitted.
    write_hook(wt.path / ".githooks", "post-commit", markers)
    require_hooks_fire(wt.path, markers)

    (wt.path / "change.txt").write_text("change\n", encoding="utf-8")
    assert manager.commit_all(wt, "T04: change") is not None

    assert fired(markers) == []


def test_signing_config_is_ignored(manager: WorktreeManager, wt_repo: Path, tmp_path: Path) -> None:
    run_git(wt_repo, "config", "commit.gpgsign", "true")
    run_git(wt_repo, "config", "tag.gpgsign", "true")
    run_git(wt_repo, "config", "gpg.program", str(tmp_path / "no-such-gpg"))
    wt = manager.create("T04", TITLE, 1)
    (wt.path / "change.txt").write_text("change\n", encoding="utf-8")

    started = time.monotonic()
    commit = manager.commit_all(wt, "T04: unsigned")
    assert time.monotonic() - started < 10
    assert commit is not None
    assert run_git(wt.path, "log", "-1", "--format=%G?").strip() == "N"

    spool_git(["tag", "-a", "t1", "-m", "x"], cwd=wt_repo).check()
    assert run_git(wt_repo, "tag", "--list", "t1").strip() == "t1"


def test_a_hooks_path_outside_the_repo_never_runs(
    manager: WorktreeManager, wt_repo: Path, markers: Path, tmp_path: Path
) -> None:
    hooks = tmp_path / "repo-hooks"
    for name in ("pre-commit", "post-checkout", "post-merge", "post-commit"):
        write_hook(hooks, name, markers)
    run_git(wt_repo, "config", "core.hooksPath", str(hooks))
    require_hooks_fire(wt_repo, markers)

    wt = manager.create("T04", TITLE, 1)  # worktree add: post-checkout
    (wt.path / "change.txt").write_text("change\n", encoding="utf-8")
    assert manager.commit_all(wt, "T04: change") is not None  # pre-commit, post-commit
    (wt_repo / "main.txt").write_text("main\n", encoding="utf-8")
    spool_git(["add", "main.txt"], cwd=wt_repo).check()
    spool_git(["commit", "--quiet", "-m", "main moves"], cwd=wt_repo).check()
    spool_git(["merge", "--no-edit", "main"], cwd=wt.path).check()  # post-merge
    spool_git(["checkout", "--quiet", "--detach", "HEAD~1"], cwd=wt.path).check()

    assert fired(markers) == []


# Spawning git anywhere but services/git/runner.py would skip the hooks and signing options.
_BYPASS = re.compile(r"""git_executable\(|which\(\s*["']git["']|[\[(]\s*["']git["']\s*,""")


def test_every_git_call_goes_through_run_git() -> None:
    src = Path(spoolhq.__file__).parent
    runner = src / "services" / "git" / "runner.py"
    offenders = [
        f"{path.relative_to(src)}:{number}: {line.strip()}"
        for path in sorted(src.rglob("*.py"))
        if path != runner
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if _BYPASS.search(line)
    ]
    assert offenders == []


def test_the_bypass_check_catches_a_direct_call() -> None:
    for line in (
        'subprocess.run(["git", "commit"])',
        "subprocess.run([git_executable(), 'merge'])",
        'shutil.which("git")',
        "cmd = ('git', 'checkout')",
    ):
        assert _BYPASS.search(line), line
    assert not _BYPASS.search('run_git(["commit", "-m", "x"], cwd)')
