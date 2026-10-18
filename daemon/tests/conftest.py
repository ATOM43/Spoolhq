import os
import shutil
import socket
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from spoolhq.api import create_app
from spoolhq.core.config import load_settings


@pytest.fixture(autouse=True)
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point SPOOLHQ_HOME at a temp dir and drop other SPOOLHQ_* variables, for every test."""
    for name in list(os.environ):
        if name.upper().startswith("SPOOLHQ_"):
            monkeypatch.delenv(name)
    path = tmp_path / "spoolhq-home"
    monkeypatch.setenv("SPOOLHQ_HOME", str(path))
    return path


@pytest.fixture(autouse=True)
def projects_dir(home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point SPOOLHQ_PROJECTS_DIR at a temp dir (not created), for every test."""
    path = tmp_path / "projects"
    monkeypatch.setenv("SPOOLHQ_PROJECTS_DIR", str(path))
    return path


def run_git(repo: Path, *args: str) -> str:
    git = shutil.which("git")
    assert git is not None, "the tests need git on PATH"
    result = subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [git, "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return result.stdout


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """A fresh repository with one commit on ``main``, independent of the user's git config."""
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init", "--quiet", "--initial-branch=main")
    run_git(
        repo,
        "-c",
        "user.name=SpoolHQ Tests",
        "-c",
        "user.email=tests@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "--quiet",
        "--allow-empty",
        "--no-verify",
        "-m",
        "initial commit",
    )
    return repo


@pytest.fixture
def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
    return port


@pytest.fixture
def token() -> str:
    return "test-token-" + "x" * 32


@pytest.fixture
def client(token: str) -> Iterator[TestClient]:
    settings = load_settings()
    app = create_app(settings, token=token)
    with TestClient(app, base_url=f"http://127.0.0.1:{settings.port}") as test_client:
        yield test_client
