"""services/git: SpoolHQ's git calls never run repository hooks and never sign."""

import subprocess
import time
from pathlib import Path

import pytest
from conftest import run_git

from spoolhq.services.git import WorktreeManager
from spoolhq.services.git import run_git as spool_git
from spoolhq.services.git.runner import git_executable

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
