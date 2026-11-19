"""services/git/runner: one git call per repository at a time, and the Windows config retry."""

import logging
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.git import runner
from tests.conftest import run_git

# The per-repository lock ----------------------------------------------------------------


def _timed_status(monkeypatch: pytest.MonkeyPatch, inside: Any = None) -> list[tuple[float, float]]:
    """Record (start, end) of every ``git status``; ``inside()`` runs while it is running."""
    spans: list[tuple[float, float]] = []
    real = runner.subprocess.run

    def run(command: list[str], **kwargs: Any) -> Any:
        if "status" not in command:
            return real(command, **kwargs)
        start = time.monotonic()
        if inside is not None:
            inside()
        result = real(command, **kwargs)
        time.sleep(0.02)
        spans.append((start, time.monotonic()))
        return result

    monkeypatch.setattr(runner.subprocess, "run", run)
    return spans


def test_calls_on_one_repo_never_overlap(wt_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spans = _timed_status(monkeypatch)

    def work() -> None:
        for _ in range(5):
            runner.run_git(["status", "--porcelain"], wt_repo).check()

    threads = [threading.Thread(target=work) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    spans.sort()
    assert len(spans) == 10
    for (_, end), (start, _) in zip(spans, spans[1:], strict=False):
        assert end <= start


def test_calls_on_two_repos_may_overlap(
    wt_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = tmp_path / "other-repo"
    other.mkdir()
    run_git(other, "init", "--quiet", "-b", "main")
    both_inside = threading.Barrier(2, timeout=10)  # breaks unless both run at once
    _timed_status(monkeypatch, inside=both_inside.wait)

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda repo: runner.run_git(["status"], repo), [wt_repo, other]))

    assert [result.returncode for result in results] == [0, 0]


def test_a_repo_and_its_worktree_share_one_lock(wt_repo: Path, tmp_path: Path) -> None:
    worktree = tmp_path / "wt"
    run_git(wt_repo, "worktree", "add", "-b", "feature", str(worktree))
    (wt_repo / "sub").mkdir()

    lock = runner.repo_lock(wt_repo)

    assert runner.repo_lock(worktree) is lock
    assert runner.repo_lock(wt_repo / "sub") is lock
    assert runner.common_dir(worktree) == (wt_repo / ".git").resolve()


def test_outside_a_repo_the_folder_is_the_key(tmp_path: Path) -> None:
    assert runner.common_dir(tmp_path) == tmp_path.absolute()
    assert runner.common_dir(tmp_path / "gone") == (tmp_path / "gone").absolute()


# The Windows config retry ---------------------------------------------------------------

CONFIG_BUSY = [
    "error: could not lock config file .git/config: File exists",
    "warning: unable to access '.git/config': Permission denied\n"
    "fatal: unknown error occurred while reading the configuration files",
    "error: opening .git/config: Permission denied",
]


def _failing(
    monkeypatch: pytest.MonkeyPatch, wt_repo: Path, stderr: str, failures: int
) -> tuple[list[list[str]], list[float]]:
    """git fails ``failures`` times with ``stderr``, then succeeds; sleeps are recorded."""
    runner.common_dir(wt_repo)  # cache the lock key before git is faked
    calls: list[list[str]] = []
    sleeps: list[float] = []

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if len(calls) <= failures:
            return subprocess.CompletedProcess(command, 128, "", stderr)
        return subprocess.CompletedProcess(command, 0, "ok", "")

    monkeypatch.setattr(runner.subprocess, "run", run)
    monkeypatch.setattr(runner.time, "sleep", sleeps.append)
    return calls, sleeps


@pytest.mark.parametrize("stderr", CONFIG_BUSY)
def test_config_busy_is_retried_on_windows(
    wt_repo: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, stderr: str
) -> None:
    monkeypatch.setattr(runner.sys, "platform", "win32")
    calls, sleeps = _failing(monkeypatch, wt_repo, stderr, failures=2)

    with caplog.at_level(logging.WARNING, logger=runner.__name__):
        result = runner.run_git(["config", "--get", "user.name"], wt_repo)

    assert (result.returncode, result.stdout) == (0, "ok")
    assert len(calls) == 3
    assert sleeps == [0.1, 0.3]
    assert [record.getMessage() for record in caplog.records] == [
        "git config busy; retrying git config"
    ] * 2


def test_config_busy_three_times_returns_the_error(
    wt_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner.sys, "platform", "win32")
    calls, sleeps = _failing(monkeypatch, wt_repo, CONFIG_BUSY[0], failures=3)

    result = runner.run_git(["branch", "-D", "x"], wt_repo)

    assert result.returncode == 128
    assert result.stderr == CONFIG_BUSY[0]
    assert len(calls) == 3
    assert sleeps == [0.1, 0.3]


def test_other_failures_are_not_retried(wt_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner.sys, "platform", "win32")
    calls, sleeps = _failing(
        monkeypatch, wt_repo, "error: open('a.txt'): Permission denied", failures=3
    )

    assert runner.run_git(["add", "a.txt"], wt_repo).returncode == 128
    assert (len(calls), sleeps) == (1, [])


@pytest.mark.parametrize("platform", ["linux", "darwin"])
def test_nothing_is_retried_off_windows(
    wt_repo: Path, monkeypatch: pytest.MonkeyPatch, platform: str
) -> None:
    monkeypatch.setattr(runner.sys, "platform", platform)
    calls, sleeps = _failing(monkeypatch, wt_repo, CONFIG_BUSY[1], failures=3)

    assert runner.run_git(["status"], wt_repo).returncode == 128
    assert (len(calls), sleeps) == (1, [])


# Stress ---------------------------------------------------------------------------------

THREADS = 20
ROUNDS = 200  # git calls in all: half branch deletes, half config/ref reads


@pytest.mark.integration
def test_config_reads_and_branch_deletes_in_parallel_never_fail(wt_repo: Path) -> None:
    """The Windows race from CI: ``branch -D`` rewrites .git/config while others read it."""
    deletes = ROUNDS // 2
    branches = [f"spoolhq/T{n:04d}-x" for n in range(deletes)]
    head = run_git(wt_repo, "rev-parse", "HEAD").strip()
    subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [runner.git_executable(), "update-ref", "--stdin"],
        cwd=wt_repo,
        # bytes: text mode would send CRLF on Windows, which update-ref refuses
        input="".join(f"create refs/heads/{name} {head}\n" for name in branches).encode(),
        check=True,
    )
    with (wt_repo / ".git" / "config").open("a", encoding="utf-8", newline="\n") as config:
        config.writelines(f'[branch "{name}"]\n\tspoolhq = 1\n' for name in branches)
    work: list[list[str]] = []
    for n, name in enumerate(branches):
        work.append(["branch", "-D", name])
        work.append(
            ["config", "--get", "user.name"]
            if n % 2 == 0
            else ["show-ref", "--verify", "--quiet", "refs/heads/main"]
        )

    with ThreadPoolExecutor(THREADS) as pool:
        results = list(pool.map(lambda args: runner.run_git(args, wt_repo), work))

    failed = [(result.args, result.stderr) for result in results if result.returncode != 0]
    assert failed == []
    assert run_git(wt_repo, "branch", "--list", "spoolhq/*").strip() == ""
