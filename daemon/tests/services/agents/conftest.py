from pathlib import Path

import pytest

from spoolhq.services.agents import AgentPolicy

STACK_COMMANDS = {"install": "just install", "lint": "just lint", "test": "just test"}


@pytest.fixture
def worktree(tmp_path: Path) -> Path:
    path = tmp_path / "worktree"
    path.mkdir()
    return path


@pytest.fixture
def user_home(tmp_path: Path) -> Path:
    """Stands in for the user's home folder (``ClaudeCliRunner(home=...)``)."""
    path = tmp_path / "user-home"
    path.mkdir()
    return path


@pytest.fixture
def policy(worktree: Path, home: Path) -> AgentPolicy:
    return AgentPolicy.for_worktree(worktree, STACK_COMMANDS, home)
