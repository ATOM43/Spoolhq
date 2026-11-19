"""``POST /api/repos/inspect``: an existing repo's branch, state and detected commands."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.conftest import run_git

pytestmark = pytest.mark.usefixtures("git_identity")


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_inspect_a_repo(client: TestClient, token: str, git_repo: Path) -> None:
    (git_repo / "justfile").write_text("install:\n\ttrue\ntest:\n\ttrue\n", encoding="utf-8")
    (git_repo / ".claude").mkdir()
    (git_repo / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
    run_git(git_repo, "remote", "add", "origin", "https://github.com/o/r.git")
    response = client.post("/api/repos/inspect", json={"path": str(git_repo)}, headers=auth(token))
    assert response.status_code == 200
    assert response.json() == {
        "branch": "main",
        "clean": False,
        "dirty": ["?? .claude/", "?? justfile"],
        "origin": "https://github.com/o/r.git",
        "commands": {
            "install": "just install",
            "lint": None,
            "test": "just test",
            "source": "justfile",
        },
        "agent_settings": [".claude/settings.json"],
        "notes_missing": ["PROGRESS.md", "DECISIONS.md"],
    }


def test_a_refused_path_names_the_path_field(
    client: TestClient, token: str, tmp_path: Path
) -> None:
    response = client.post("/api/repos/inspect", json={"path": str(tmp_path)}, headers=auth(token))
    assert response.status_code == 422
    body = response.json()["error"]
    assert (body["field"], body["message"]) == ("path", "Not a git repository")


def test_inspect_needs_the_token(client: TestClient, git_repo: Path) -> None:
    assert client.post("/api/repos/inspect", json={"path": str(git_repo)}).status_code == 401
