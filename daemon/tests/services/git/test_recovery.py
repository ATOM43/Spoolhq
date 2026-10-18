"""services/git: worktree crash recovery, including a process killed mid-run."""

import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

from spoolhq.services.git import RecoveryAction, WorktreeManager, recover_worktrees
from spoolhq.services.git.worktrees import parse_worktree_list, remove_path
from tests.conftest import run_git


def branches(repo: Path) -> list[str]:
    return run_git(repo, "branch", "--list", "--format=%(refname:short)").split()


def registered(repo: Path) -> list[Path]:
    output = run_git(repo, "worktree", "list", "--porcelain", "-z")
    return [Path(os.path.realpath(entry.path)) for entry in parse_worktree_list(output)]


def real(path: Path) -> Path:
    return Path(os.path.realpath(path))


def test_recovery_cleans_up_and_keeps_what_it_must(
    manager: WorktreeManager,
    wt_repo: Path,
    wt_root: Path,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # (a) a registered T04 worktree left behind, not kept
    a = manager.create("T04", "left behind", 1)
    # (b) a T05 worktree whose folder was deleted by hand
    b = manager.create("T05", "deleted by hand", 2)
    remove_path(b.path)
    # (c) a folder git doesn't know
    c = wt_root / "demo" / "T06"
    c.mkdir()
    (c / "leftover.txt").write_text("x\n", encoding="utf-8")
    # (d) a registered T07 worktree that must stay
    d = manager.create("T07", "blocked run", 4)
    # (e) a worktree outside the root, made directly with git
    e = tmp_path / "elsewhere" / "T09"
    run_git(wt_repo, "worktree", "add", "--quiet", "-b", "feat/T09-outside", str(e))
    # (f) a worktree under the root on a branch without the marker, made with git
    f = wt_root / "demo" / "T08"
    run_git(wt_repo, "worktree", "add", "--quiet", "-b", "feat/T08-unmarked", str(f))

    caplog.set_level(logging.INFO)
    report = recover_worktrees(manager, keep=lambda ticket_id: ticket_id == "T07")

    assert report.pruned == ["T05"]
    assert report.removed == ["T04", "T08"]
    assert report.removed_orphan == ["T06"]
    assert report.kept == ["T07"]
    assert report.failed == []
    by_ticket = {entry.ticket_id: entry for entry in report.entries}
    assert by_ticket["T05"].path == b.path
    assert by_ticket["T05"].reason == "its folder was missing"
    assert "feat/T08-unmarked has no SpoolHQ marker" in by_ticket["T08"].reason

    # a: removed with its branch
    assert not a.path.exists()
    assert a.branch not in branches(wt_repo)
    # b: no longer registered
    assert real(b.path) not in registered(wt_repo)
    # c: deleted
    assert not c.exists()
    # d: still there and resumable
    assert d.path.is_dir()
    assert manager.resume("T07") == d
    # e: untouched
    assert e.is_dir()
    assert real(e) in registered(wt_repo)
    assert "feat/T09-outside" in branches(wt_repo)
    # f: worktree removed, the unmarked branch kept
    assert not f.exists()
    assert real(f) not in registered(wt_repo)
    assert "feat/T08-unmarked" in branches(wt_repo)

    lines = [r for r in caplog.records if r.name == "spoolhq.services.git.recovery"]
    assert sorted((r.__dict__["ticket_id"], r.__dict__["action"]) for r in lines) == [
        ("T04", "removed"),
        ("T05", "pruned"),
        ("T06", "removed_orphan"),
        ("T07", "kept"),
        ("T08", "removed"),
    ]

    again = recover_worktrees(manager, keep=lambda ticket_id: ticket_id == "T07")
    assert [(entry.ticket_id, entry.action) for entry in again.entries] == [
        ("T07", RecoveryAction.KEPT)
    ]


def test_recovery_reports_a_worktree_it_cannot_remove(
    manager: WorktreeManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager.create("T04", "stuck", 1)

    def stuck(*args: object, **kwargs: object) -> None:
        raise OSError("file in use")

    monkeypatch.setattr(manager, "teardown", stuck)
    report = recover_worktrees(manager, keep=lambda ticket_id: False)
    assert report.failed == ["T04"]
    assert report.entries[0].reason == "file in use"


def test_recovery_with_no_root_does_nothing(manager: WorktreeManager, wt_root: Path) -> None:
    assert recover_worktrees(manager, keep=lambda ticket_id: False).entries == ()
    assert not wt_root.exists()


CRASHING_RUN = """
import sys
import time
from pathlib import Path

from spoolhq.services.git import WorktreeManager

manager = WorktreeManager(Path(sys.argv[1]), "demo", "main", Path(sys.argv[2]))
wt = manager.create("T04", "Crash mid-run", "1")
(wt.path / "half-done.txt").write_text("work in progress\\n", encoding="utf-8")
print("ready", flush=True)
time.sleep(120)
"""


@pytest.mark.integration
def test_worktree_of_a_killed_process_is_recovered(
    manager: WorktreeManager, wt_repo: Path, wt_root: Path
) -> None:
    proc = subprocess.Popen(  # noqa: S603 - fixed argument list, no shell
        [sys.executable, "-c", CRASHING_RUN, str(wt_repo), str(wt_root)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert proc.stdout is not None
        line = proc.stdout.readline()
        assert line.strip() == "ready", proc.stderr.read() if proc.stderr else ""
    finally:
        proc.kill()
        proc.wait(timeout=30)
        for stream in (proc.stdout, proc.stderr):
            if stream is not None:
                stream.close()

    wt_path = wt_root / "demo" / "T04"
    assert wt_path.is_dir()
    report = recover_worktrees(manager, keep=lambda ticket_id: False)

    assert report.removed == ["T04"]
    assert not wt_path.exists()
    assert branches(wt_repo) == ["main"]
    assert registered(wt_repo) == [real(wt_repo)]
