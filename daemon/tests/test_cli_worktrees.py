"""`spool worktrees list`: read-only view of a project's worktrees."""

from pathlib import Path

from typer.testing import CliRunner

from spoolhq.cli import app
from spoolhq.core.config import load_settings
from spoolhq.services.git import WorktreeManager
from spoolhq.services.git.worktrees import remove_path

runner = CliRunner()


def test_list_shows_state(git_repo: Path, workspace: Path) -> None:
    manager = WorktreeManager(git_repo, "demo", "main", load_settings().worktrees_dir)

    result = runner.invoke(app, ["worktrees", "list", "demo"])
    assert result.exit_code == 0, result.output
    assert result.output == "No worktrees in 'demo'.\n"

    wt = manager.create("T04", "Say hi", 1)
    result = runner.invoke(app, ["worktrees", "list", "demo"])
    assert result.exit_code == 0, result.output
    header, row = result.output.splitlines()
    assert header.split() == ["TICKET", "BRANCH", "PATH", "STATE"]
    assert row.split() == ["T04", "feat/T04-say-hi", str(wt.path), "ok"]

    remove_path(wt.path)
    result = runner.invoke(app, ["worktrees", "list", "demo"])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[1].endswith("missing folder")
    # Listing changed nothing: git still has the entry.
    assert manager.list_worktrees()[0].registered


def test_list_shows_unregistered_folders(workspace: Path) -> None:
    folder = load_settings().worktrees_dir / "demo" / "T06"
    folder.mkdir(parents=True)
    result = runner.invoke(app, ["worktrees", "list", "demo"])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[1].split() == ["T06", "-", str(folder), "not", "registered"]


def test_unknown_project_exits_1(projects_dir: Path) -> None:
    result = runner.invoke(app, ["worktrees", "list", "nope"])
    assert result.exit_code == 1
    assert result.output == f"error: no project 'nope' in {projects_dir}\n"


def test_invalid_project_exits_1(workspace: Path, git_repo: Path, tmp_path: Path) -> None:
    git_repo.rename(tmp_path / "moved")
    result = runner.invoke(app, ["worktrees", "list", "demo"])
    assert result.exit_code == 1
    assert result.output.startswith("error: project.yaml: repo: path does not exist")
