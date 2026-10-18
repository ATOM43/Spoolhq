from pathlib import Path

import pytest

from spoolhq.services.git import WorktreeManager
from tests.conftest import commit_file, run_git


@pytest.fixture
def wt_repo(tmp_path: Path, isolated_git: None) -> Path:
    """A repository on ``main`` with a local identity and one commit holding README.md."""
    repo = tmp_path / "main-repo"
    repo.mkdir()
    run_git(repo, "init", "--quiet", "-b", "main")
    run_git(repo, "config", "user.name", "SpoolHQ Tests")
    run_git(repo, "config", "user.email", "tests@example.invalid")
    run_git(repo, "config", "commit.gpgsign", "false")
    commit_file(repo, "README.md", "# demo\n", "initial commit")
    return repo


@pytest.fixture
def wt_root(tmp_path: Path) -> Path:
    return tmp_path / "worktrees"


@pytest.fixture
def manager(wt_repo: Path, wt_root: Path) -> WorktreeManager:
    return WorktreeManager(wt_repo, "demo", "main", wt_root)
