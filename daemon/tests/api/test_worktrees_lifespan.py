"""Daemon wiring for worktrees: startup recovery and the keep rule built from the run log."""

import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from spoolhq.api import create_app
from spoolhq.api import worktrees as api_worktrees
from spoolhq.core.config import load_settings
from spoolhq.services.git import GitError, RecoveryReport, WorktreeManager
from spoolhq.services.projects import init_project
from spoolhq.services.runs import RunLog, RunStatus
from tests.conftest import commit_file, run_git


def make_repo(path: Path) -> Path:
    path.mkdir()
    run_git(path, "init", "--quiet", "-b", "main")
    run_git(path, "config", "user.name", "SpoolHQ Tests")
    run_git(path, "config", "user.email", "tests@example.invalid")
    commit_file(path, "README.md", "# repo\n", "initial commit")
    return path


def test_startup_recovers_worktrees_and_skips_a_broken_project(
    tmp_path: Path,
    projects_dir: Path,
    token: str,
    isolated_git: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    settings = load_settings()
    alpha_repo = make_repo(tmp_path / "alpha-repo")
    beta_repo = make_repo(tmp_path / "beta-repo")
    init_project("alpha", alpha_repo, projects_dir=projects_dir)
    init_project("beta", beta_repo, projects_dir=projects_dir)
    beta_repo.rename(tmp_path / "beta-repo-moved")

    manager = WorktreeManager(alpha_repo, "alpha", "main", settings.worktrees_dir)
    stale = manager.create("T04", "stale", 1)
    blocked = manager.create("T05", "blocked", 2)
    with RunLog(projects_dir / "alpha", daemon_instance="previous") as log:
        log.start_run("T04")
        log.set_run_status(log.start_run("T05").id, RunStatus.BLOCKED, "gates failed")

    app = create_app(settings, token=token)
    caplog.set_level(logging.INFO)
    with TestClient(app, base_url=f"http://127.0.0.1:{settings.port}") as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        reports: dict[str, RecoveryReport] = app.state.worktree_recovery
        assert sorted(reports) == ["alpha"]
        assert reports["alpha"].removed == ["T04"]
        assert reports["alpha"].kept == ["T05"]

    assert not stale.path.exists()
    assert stale.branch not in run_git(alpha_repo, "branch", "--list")
    assert blocked.path.is_dir()
    assert manager.resume("T05") == blocked

    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert [r.getMessage() for r in errors] == ["cannot recover worktrees; skipping this project"]
    assert errors[0].__dict__["project"] == "beta"
    assert "path does not exist" in errors[0].__dict__["error"]


def test_awaiting_approval_keeps_and_done_removes(
    git_repo: Path, workspace: Path, token: str
) -> None:
    settings = load_settings()
    manager = WorktreeManager(git_repo, "demo", "main", settings.worktrees_dir)
    for ticket_id in ("T04", "T05", "T06"):
        manager.create(ticket_id, "work", 1)
    with RunLog(workspace, daemon_instance="previous") as log:
        log.set_run_status(log.start_run("T04").id, RunStatus.AWAITING_APPROVAL)
        log.set_run_status(log.start_run("T05").id, RunStatus.BLOCKED)
        log.set_run_status(log.start_run("T05").id, RunStatus.DONE)

    with TestClient(create_app(settings, token=token), base_url="http://127.0.0.1:8765") as client:
        report = client.app.state.worktree_recovery["demo"]  # type: ignore[attr-defined]
        assert report.kept == ["T04"]
        assert report.removed == ["T05", "T06"]


def test_keep_rule(workspace: Path) -> None:
    with RunLog(workspace, daemon_instance="current") as log:
        keep = api_worktrees.keep_for(log)
        assert keep("T04") is False
        run = log.start_run("T04")
        assert keep("T04") is False
        log.set_run_status(run.id, RunStatus.BLOCKED)
        assert keep("T04") is True
        assert keep("notes") is False
    assert keep("T04") is True  # a closed run log can't be read: keep the worktree


def test_old_git_is_logged_and_the_daemon_serves(
    token: str, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def too_old() -> tuple[int, int, int]:
        raise GitError("git 2.36 or newer is required (found 2.34.1)")

    monkeypatch.setattr(api_worktrees, "check_git_version", too_old)
    settings = load_settings()
    with TestClient(create_app(settings, token=token), base_url="http://127.0.0.1:8765") as client:
        assert client.get("/api/health").status_code == 200
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert [r.__dict__["error"] for r in errors] == ["git 2.36 or newer is required (found 2.34.1)"]


def test_project_without_a_run_log_is_skipped(
    workspace: Path, projects_dir: Path, caplog: pytest.LogCaptureFixture
) -> None:
    from spoolhq.services.runs import RunRegistry

    registry = RunRegistry("instance")  # nothing opened
    settings = load_settings()
    assert api_worktrees.recover_all_worktrees(projects_dir, settings.worktrees_dir, registry) == {}
    assert "no run log; skipping worktree recovery for this project" in caplog.messages
