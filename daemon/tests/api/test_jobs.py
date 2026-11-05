"""``POST /api/projects`` starts a creation job; ``/api/jobs`` reads and cancels it."""

import os
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from spoolhq.cli import app
from spoolhq.services.creation import NAME_RULE
from tests.conftest import fake_tool_cmd, run_git

pytestmark = pytest.mark.usefixtures("git_identity")
PASS = {gate: fake_tool_cmd("pass") for gate in ("install", "lint", "test")}


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def post(client: TestClient, token: str, **body: Any) -> Any:
    return client.post("/api/projects", json={"name": "demo", **body}, headers=auth(token))


def finished(client: TestClient, token: str, job_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + 60
    while True:
        job = client.get(f"/api/jobs/{job_id}", headers=auth(token)).json()
        if job["state"] != "running":
            return job  # type: ignore[no-any-return]
        assert time.monotonic() < deadline
        time.sleep(0.05)


def refused(client: TestClient, token: str, **body: Any) -> str:
    response = post(client, token, **body)
    assert response.status_code == 422, response.text
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert client.app.state.creation._jobs == {}  # type: ignore[attr-defined]
    return error["field"]  # type: ignore[no-any-return]


def test_create_an_empty_project_and_poll_it(
    client: TestClient, token: str, tmp_path: Path, projects_dir: Path
) -> None:
    repo = tmp_path / "new"
    response = post(client, token, source="empty", repo_path=str(repo))
    assert response.status_code == 202
    job = finished(client, token, response.json()["job_id"])
    assert job["state"] == "succeeded"
    assert job["project"] == "demo"
    assert [(s["name"], s["state"]) for s in job["steps"]] == [
        ("workspace", "passed"),
        ("repo", "passed"),
        ("commands", "skipped"),
        ("commit", "passed"),
    ]
    assert all(s["duration_s"] is not None for s in job["steps"])
    assert job["rollback"] is None
    assert run_git(repo, "log", "--format=%s").strip() == "Initial commit (SpoolHQ)"

    # No test command: the panel says why, and the scheduler refuses to run.
    detail = client.get("/api/projects/demo", headers=auth(token)).json()
    assert detail["next_ticket"] is None
    assert detail["idle"]["code"] == "no_commands"
    assert detail["idle"]["message"] == "Set the stack commands in project.yaml first"
    run = client.post("/api/projects/demo/run/next", headers=auth(token))
    assert run.status_code == 409
    assert run.json()["error"]["message"] == "Set the stack commands in project.yaml first"
    plan = client.post("/api/projects/demo/plan/generate", headers=auth(token))
    assert plan.status_code == 409


@pytest.mark.integration
def test_a_failing_test_command_and_its_rollback(
    client: TestClient, token: str, git_repo: Path, projects_dir: Path
) -> None:
    commands = {**PASS, "test": fake_tool_cmd("fail-test")}
    response = post(client, token, source="existing", repo_path=str(git_repo), commands=commands)
    job = finished(client, token, response.json()["job_id"])
    assert job["state"] == "failed"
    step = job["steps"][2]
    assert (step["state"], step["field"]) == ("failed", "commands.test")
    assert "FAILED tests/test_math.py::test_add" in step["output"]
    assert job["rollback"]["left"] == []
    assert job["rollback"]["removed"] == [str(projects_dir / "demo"), str(projects_dir)]
    assert not projects_dir.exists()


@pytest.mark.integration
def test_cancel_a_running_job(
    client: TestClient, token: str, tmp_path: Path, projects_dir: Path
) -> None:
    body = {"source": "empty", "repo_path": str(tmp_path / "new")}
    job_id = post(client, token, **body, commands={"test": fake_tool_cmd("sleep")}).json()["job_id"]
    deadline = time.monotonic() + 30
    while (
        client.get(f"/api/jobs/{job_id}", headers=auth(token)).json()["steps"][2]["state"]
        != "running"
    ):
        assert time.monotonic() < deadline
        time.sleep(0.05)
    job = client.post(f"/api/jobs/{job_id}/cancel", headers=auth(token)).json()
    assert job["state"] == "cancelled"
    assert not (tmp_path / "new").exists()


def test_unknown_jobs(client: TestClient, token: str) -> None:
    assert client.get(f"/api/jobs/{'0' * 32}", headers=auth(token)).status_code == 404
    assert client.post(f"/api/jobs/{'0' * 32}/cancel", headers=auth(token)).status_code == 404
    assert client.get("/api/jobs/../x", headers=auth(token)).status_code in (404, 422)
    assert client.get(f"/api/jobs/{'0' * 32}").status_code == 401


@pytest.mark.parametrize("name", ["VW", "1abc", "a_b", "a" * 41])
def test_bad_names(client: TestClient, token: str, tmp_path: Path, name: str) -> None:
    response = post(client, token, name=name, source="empty", repo_path=str(tmp_path / "n"))
    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "validation_error",
        "message": NAME_RULE,
        "field": "name",
    }


def test_unsafe_requests_start_no_job(
    client: TestClient,
    token: str,
    tmp_path: Path,
    git_repo: Path,
    projects_dir: Path,
    home: Path,
) -> None:
    empty = {"source": "empty"}
    for path in (os.path.abspath(os.sep), str(Path.home()), str(projects_dir / "x"), str(home)):
        assert refused(client, token, **empty, repo_path=path) == "repo_path"
    link = tmp_path / "link"
    try:
        link.symlink_to(tmp_path, target_is_directory=True)
        assert refused(client, token, **empty, repo_path=str(link)) == "repo_path"
    except OSError:
        pass  # Windows without symlink rights
    full = tmp_path / "full"
    full.mkdir()
    (full / "a.txt").write_text("x", encoding="utf-8")
    template = {"source": "template", "commands": PASS}
    assert refused(client, token, **template, template="fastapi-react", repo_path=str(full)) == (
        "repo_path"
    )
    new = str(tmp_path / "new")
    assert refused(client, token, **template, template="nope", repo_path=new) == "template"
    url = "https://github.com/o/t.git"
    assert refused(client, token, **template, template=url, repo_path=new) == "template"
    (git_repo / "dirty.txt").write_text("x", encoding="utf-8")
    existing = {"source": "existing", "repo_path": str(git_repo), "commands": PASS}
    assert refused(client, token, **existing) == "repo_path"
    (projects_dir / "demo").mkdir(parents=True)
    assert refused(client, token, **empty, repo_path=new) == "name"
    response = post(client, token, source="nope", repo_path=new)
    assert (response.status_code, response.json()["error"]["field"]) == (422, "source")


def test_the_cli_and_the_api_make_the_same_workspace(
    client: TestClient, token: str, tmp_path: Path, projects_dir: Path
) -> None:
    def files() -> dict[str, str]:
        workspace = projects_dir / "demo"
        return {
            p.relative_to(workspace).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(workspace.rglob("*"))
            if p.is_file()
        }

    repo = tmp_path / "new"
    options = ["--source", "empty", "--merge-preset", "always_pr", "--clickup-list", "42"]
    result = CliRunner().invoke(app, ["init", "demo", "--repo", str(repo), *options])
    assert result.exit_code == 0, result.output
    from_cli = files()
    for path in (projects_dir / "demo", repo):
        from spoolhq.services.git import remove_path

        remove_path(path)
    body = {"source": "empty", "repo_path": str(repo), "merge_preset": "always_pr"}
    job_id = post(client, token, **body, clickup_list_id="42").json()["job_id"]
    assert finished(client, token, job_id)["state"] == "succeeded"
    assert files() == from_cli
    assert "protected_paths: ['**']" in from_cli["project.yaml"]
