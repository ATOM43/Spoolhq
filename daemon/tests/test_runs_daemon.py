"""Daemon wiring: startup recovery in the lifespan, the run registry and the instance lock."""

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from spoolhq.api import create_app
from spoolhq.core.config import load_settings
from spoolhq.core.daemon_lock import DaemonAlreadyRunning, acquire_daemon_lock, lock_path
from spoolhq.services.projects import init_project, list_workspaces
from spoolhq.services.runs import (
    INTERRUPTED_REASON,
    AttemptKind,
    RunLog,
    RunRegistry,
    RunStatus,
    state_db_path,
)


def make_workspace(name: str, repo: Path, projects_dir: Path) -> Path:
    return init_project(name, repo, projects_dir=projects_dir).path


# Lifespan -----------------------------------------------------------------------------


def test_startup_recovers_and_skips_a_corrupt_database(
    git_repo: Path, projects_dir: Path, token: str, caplog: pytest.LogCaptureFixture
) -> None:
    good = make_workspace("alpha", git_repo, projects_dir)
    broken = make_workspace("beta", git_repo, projects_dir)
    with RunLog(good, daemon_instance="previous") as log:
        stale = log.start_run("T04")
        log.start_attempt(stale.id, AttemptKind.INITIAL)
    broken_db = state_db_path(broken)
    broken_db.parent.mkdir()
    broken_db.write_text("not a database\n" * 50, encoding="utf-8")

    settings = load_settings()
    app = create_app(settings, token=token)
    caplog.set_level(logging.INFO)
    with TestClient(app, base_url=f"http://127.0.0.1:{settings.port}") as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        registry: RunRegistry = app.state.runs
        assert registry.projects == ["alpha"]
        assert registry.daemon_instance == app.state.daemon_instance
        assert len(app.state.daemon_instance) == 32
        run = registry.get("alpha").run_log.get_run(stale.id)
        assert run.status is RunStatus.INTERRUPTED
        assert run.reason == INTERRUPTED_REASON
        with pytest.raises(KeyError, match="no run log for project 'beta'"):
            registry.get("beta")

    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errors) == 1
    assert errors[0].__dict__["path"] == str(broken_db)
    assert "not a SpoolHQ database" in errors[0].__dict__["error"]
    recovered = [
        r for r in caplog.records if r.getMessage() == "run interrupted by a daemon restart"
    ]
    assert [(r.__dict__["project"], r.__dict__["run_id"]) for r in recovered] == [
        ("alpha", stale.id)
    ]

    # Shutdown closed the run log, so the file can be opened (and deleted) again.
    with RunLog.open_read_only(good) as reader:
        assert reader.get_run(stale.id).status is RunStatus.INTERRUPTED


def test_startup_without_a_projects_folder_serves(client: TestClient) -> None:
    assert client.get("/api/health").status_code == 200
    assert client.app.state.runs.projects == []  # type: ignore[attr-defined]


def test_registry_keeps_one_log_and_bus_per_workspace(git_repo: Path, projects_dir: Path) -> None:
    make_workspace("alpha", git_repo, projects_dir)
    make_workspace("beta", git_repo, projects_dir)
    registry = RunRegistry.start(projects_dir, daemon_instance="now")
    try:
        alpha, beta = registry.get("alpha"), registry.get("beta")
        assert alpha.bus is not beta.bus
        assert alpha.run_log.bus is alpha.bus
        assert alpha.run_log.daemon_instance == "now"
        with alpha.bus.subscribe() as sub:
            alpha.run_log.start_run("T01")
            assert sub.get(timeout=1) is not None
    finally:
        registry.close()
    with pytest.raises(KeyError):
        registry.get("alpha")


def test_recovery_failure_skips_the_workspace(
    git_repo: Path,
    projects_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import sqlite3

    make_workspace("alpha", git_repo, projects_dir)

    def fail(run_log: RunLog) -> list[object]:
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr("spoolhq.services.runs.registry.recover_interrupted", fail)
    registry = RunRegistry.start(projects_dir, daemon_instance="now")
    assert registry.projects == []
    assert "cannot recover interrupted runs" in caplog.text


def test_list_workspaces_skips_non_projects(git_repo: Path, projects_dir: Path) -> None:
    assert list_workspaces(projects_dir) == []
    alpha = make_workspace("alpha", git_repo, projects_dir)
    (projects_dir / ".alpha.x1.tmp").mkdir()
    (projects_dir / "notes").mkdir()
    (projects_dir / "Bad Name").mkdir()
    (projects_dir / "README.md").write_text("hi", encoding="utf-8")
    assert list_workspaces(projects_dir) == [alpha]


# Single-instance lock -----------------------------------------------------------------


def test_second_acquire_names_the_holder(home: Path) -> None:
    with acquire_daemon_lock(home) as lock:
        assert lock.held
        assert lock_path(home).read_text(encoding="ascii").strip() == str(os.getpid())
        with pytest.raises(DaemonAlreadyRunning) as info:
            acquire_daemon_lock(home)
        assert str(info.value) == (f"another SpoolHQ daemon is already running (pid {os.getpid()})")
    assert not lock.held
    lock.release()

    again = acquire_daemon_lock(home)
    again.release()


def test_unknown_holder_pid(home: Path) -> None:
    assert str(DaemonAlreadyRunning(None)) == (
        "another SpoolHQ daemon is already running (pid unknown)"
    )
    with acquire_daemon_lock(home):
        # Overwrite the pid, as a holder that crashed mid-write would leave it.
        with lock_path(home).open("r+b") as file:
            file.write(b"garbage")
        with pytest.raises(DaemonAlreadyRunning, match=r"\(pid unknown\)"):
            acquire_daemon_lock(home)


HOLD_LOCK = """
import os, sys, time
from pathlib import Path
from spoolhq.core.daemon_lock import acquire_daemon_lock

lock = acquire_daemon_lock(Path(sys.argv[1]))
print("locked", os.getpid(), flush=True)
time.sleep(600)
"""


@pytest.mark.integration
def test_serve_refuses_while_another_daemon_holds_the_lock(home: Path, free_port: int) -> None:
    holder = subprocess.Popen(  # noqa: S603 - fixed argument list, no shell
        [sys.executable, "-c", HOLD_LOCK, str(home)],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None
        # On Windows a venv's python.exe is a launcher, so the holder reports its own pid.
        word, pid = holder.stdout.readline().split()
        assert word == "locked"
        result = subprocess.run(  # noqa: S603 - fixed argument list, no shell
            [sys.executable, "-m", "spoolhq", "serve", "--port", str(free_port)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
    finally:
        holder.kill()
        holder.communicate(timeout=30)

    assert result.returncode == 1
    assert f"another SpoolHQ daemon is already running (pid {pid})" in result.stderr, result.stderr
    # The holder died, and the OS released its lock with it (possibly a moment later,
    # when the launcher's child exits on Windows).
    deadline = time.monotonic() + 30
    while True:
        try:
            acquire_daemon_lock(home).release()
            break
        except DaemonAlreadyRunning:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.1)
