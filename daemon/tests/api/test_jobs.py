"""``POST /api/projects`` starts a creation job; ``/api/jobs`` reads and cancels it."""

import os
import shlex
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from spoolhq.cli import app
from spoolhq.services.creation import NAME_RULE, Job, Rollback
from tests.conftest import fake_tool_cmd, make_template, run_git

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
    folder = make_template(tmp_path / "local-template")
    assert refused(client, token, **template, template=str(folder), repo_path=new) == "template"
    # The CLI-only options aren't part of the request (DECISIONS 345).
    for extra in ({"template_ref": "main"}, {"branch": "dev"}):
        response = post(client, token, **template, template="fixture", repo_path=new, **extra)
        assert (response.status_code, response.json()["error"]["field"]) == (422, *extra)
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


def test_a_project_being_created_is_reported_as_creating(
    client: TestClient, token: str, projects_dir: Path
) -> None:
    folder = projects_dir / "demo"
    folder.mkdir(parents=True)
    # Half written: as a job's own project.yaml is before its repo exists.
    (folder / "project.yaml").write_text("name: demo\nrepo: relative\n", encoding="utf-8")
    jobs = client.app.state.creation  # type: ignore[attr-defined]
    job = Job(id="a" * 32, project="demo", source="empty")
    jobs._jobs[job.id] = (job, threading.Event(), threading.Thread())
    for answer in (
        client.get("/api/projects", headers=auth(token)).json()[0],
        client.get("/api/projects/demo", headers=auth(token)).json(),
    ):
        assert answer["run_state"] == "creating"
        assert answer["job_id"] == job.id
        assert answer["settings_error"] is None
        assert answer["needs_you"] == 0
    job.state = "succeeded"
    listed = client.get("/api/projects", headers=auth(token)).json()[0]
    assert (listed["run_state"], listed["job_id"]) == ("idle", None)
    assert listed["settings_error"]["field"] == "repo"


@pytest.mark.integration
def test_a_rolled_back_project_is_gone_from_the_list(
    client: TestClient, token: str, tmp_path: Path
) -> None:
    commands = {"test": fake_tool_cmd("fail-test")}
    body = {"source": "empty", "repo_path": str(tmp_path / "new"), "commands": commands}
    job = finished(client, token, post(client, token, **body).json()["job_id"])
    assert job["state"] == "failed"
    assert job["steps"][2]["field"] == "commands.test"
    assert client.get("/api/projects", headers=auth(token)).json() == []


def _ended(jobs: Any, job_id: str, project: str, left: list[str]) -> Job:
    job = Job(id=job_id, project=project, source="empty", state="failed")
    job.rollback, job.ended_at = Rollback(left=left), time.monotonic()
    jobs._jobs[job.id] = (job, threading.Event(), threading.Thread())
    return job


def test_a_rollback_that_left_paths_is_listed_until_dismissed(
    client: TestClient, token: str, projects_dir: Path
) -> None:
    jobs = client.app.state.creation  # type: ignore[attr-defined]
    _ended(jobs, "b" * 32, "gone", ["/code/gone"])
    _ended(jobs, "c" * 32, "clean", [])
    (projects_dir / "half").mkdir(parents=True)  # its workspace was left behind too
    _ended(jobs, "d" * 32, "half", [str(projects_dir / "half")])
    listed = {p["name"]: p for p in client.get("/api/projects", headers=auth(token)).json()}
    assert set(listed) == {"gone", "half"}
    assert (listed["gone"]["run_state"], listed["gone"]["job_id"]) == ("cleanup_failed", "b" * 32)
    assert listed["gone"]["left"] == ["/code/gone"]
    assert listed["half"]["left"] == [str(projects_dir / "half")]

    answer = client.post(f"/api/jobs/{'b' * 32}/dismiss", headers=auth(token))
    assert answer.status_code == 204
    names = [p["name"] for p in client.get("/api/projects", headers=auth(token)).json()]
    assert names == ["half"]
    assert client.post(f"/api/jobs/{'b' * 32}/dismiss", headers=auth(token)).status_code == 404


def test_a_running_job_is_not_dismissed(client: TestClient, token: str) -> None:
    jobs = client.app.state.creation  # type: ignore[attr-defined]
    job = Job(id="e" * 32, project="demo", source="empty")
    jobs._jobs[job.id] = (job, threading.Event(), threading.Thread())
    assert client.post(f"/api/jobs/{job.id}/dismiss", headers=auth(token)).status_code == 204
    assert job.id in jobs._jobs
    job.state = "succeeded"  # the client's shutdown would join its unstarted thread


@pytest.mark.integration
@pytest.mark.skipif(sys.platform == "win32" or os.geteuid() == 0, reason="POSIX permissions")
def test_a_read_only_path_the_rollback_cant_delete_is_listed(
    client: TestClient, token: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from spoolhq.services.git import worktrees

    def give_up(func: Any, path: str, exc: BaseException) -> None:
        raise exc

    # remove_path would make the folder writable and retry: as if that chmod failed.
    monkeypatch.setattr(worktrees, "_clear_read_only_and_retry", give_up)
    holder = tmp_path / "holder"
    holder.mkdir()
    repo = holder / "new"
    script = tmp_path / "lock.py"
    script.write_text(
        "import os, pathlib, sys\n"
        "pathlib.Path('kept.txt').write_text('x', encoding='utf-8')\n"
        "os.chmod('.', 0o555)\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )
    commands = {"test": shlex.join([Path(sys.executable).as_posix(), script.as_posix()])}
    body = {"source": "empty", "repo_path": str(repo), "commands": commands}
    try:
        job = finished(client, token, post(client, token, **body).json()["job_id"])
    finally:
        os.chmod(repo, 0o700)  # writable again, so tmp_path can be removed
    assert job["state"] == "failed"
    assert job["rollback"]["left"]
    listed = client.get("/api/projects", headers=auth(token)).json()
    assert [(p["name"], p["run_state"]) for p in listed] == [("demo", "cleanup_failed")]
    assert listed[0]["left"] == job["rollback"]["left"]
