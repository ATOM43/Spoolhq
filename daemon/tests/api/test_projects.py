"""Project, settings and spec endpoints: listing, creating, and edits with ETags."""

import hashlib
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from spoolhq.api.routers import projects as projects_router
from spoolhq.services.projects import load_project, save_project
from tests.conftest import fake_tool_cmd, run_git


def auth(token: str, **headers: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", **headers}


def etag(path: Path) -> str:
    return f'"{hashlib.sha256(path.read_bytes()).hexdigest()}"'


def error(response: object) -> dict[str, str]:
    body = response.json()  # type: ignore[attr-defined]
    assert set(body) == {"error"}
    return body["error"]  # type: ignore[no-any-return]


def test_list_and_get_projects(run_client: TestClient, token: str, run_project: Path) -> None:
    (run_project / "tickets" / "T08-bad.md").write_text("no frontmatter", encoding="utf-8")
    listed = run_client.get("/api/projects", headers=auth(token))
    assert listed.status_code == 200
    assert listed.json() == [
        {
            "name": "demo",
            "done": 0,
            "total": 1,
            "run_state": "idle",
            "needs_you": 0,
            "latest_seq": 0,
            "draft": 0,
            "remaining_h": 1.0,
            "has_spec": False,
            "template": None,
            "run": None,
            "run_step": None,
            "last_activity": None,
            "usage": {"tokens": 0, "cost_usd": None},
            "settings_error": None,
            "job_id": None,
        }
    ]
    detail = run_client.get("/api/projects/demo", headers=auth(token)).json()
    assert detail["default_branch"] == "main"
    assert detail["invalid_tickets"] == 1
    assert detail["remote"] is None
    assert detail["next_ticket"] == "T07"
    assert detail["idle"] is None
    assert detail["remaining_h"] == 1


def test_project_detail_says_why_nothing_can_run(
    run_client: TestClient, token: str, run_project: Path
) -> None:
    ticket = run_project / "tickets" / "T07-parse-slug.md"
    ticket.write_text(
        ticket.read_text(encoding="utf-8").replace("status: ready", "status: draft"),
        encoding="utf-8",
    )
    detail = run_client.get("/api/projects/demo", headers=auth(token)).json()
    assert detail["next_ticket"] is None
    assert detail["idle"]["code"] == "plan_not_approved"
    assert detail["idle"]["ticket_ids"] == ["T07"]
    ticket.write_text(
        ticket.read_text(encoding="utf-8").replace("depends_on: []", "depends_on: [T99]"),
        encoding="utf-8",
    )
    idle = run_client.get("/api/projects/demo", headers=auth(token)).json()["idle"]
    assert idle["code"] == "invalid_plan"
    assert "T99" in idle["message"]


def test_unknown_or_invalid_project_names(run_client: TestClient, token: str) -> None:
    missing = run_client.get("/api/projects/nope", headers=auth(token))
    assert missing.status_code == 404
    assert error(missing) == {"code": "not_found", "message": "no project 'nope'"}
    invalid = run_client.get("/api/projects/Not_A_Slug/spec", headers=auth(token))
    assert invalid.status_code == 422
    assert error(invalid)["code"] == "validation_error"
    assert error(invalid)["field"] == "name"


def test_spec_edit_with_etags(run_client: TestClient, token: str, run_project: Path) -> None:
    spec = run_project / "CONTEXT.md"
    got = run_client.get("/api/projects/demo/spec", headers=auth(token))
    assert got.status_code == 200
    first = got.headers["ETag"]
    assert first == etag(spec)
    assert got.json() == {"content": spec.read_text(encoding="utf-8")}

    missing = run_client.put("/api/projects/demo/spec", json={"content": "x"}, headers=auth(token))
    assert (missing.status_code, error(missing)["code"]) == (428, "precondition_required")

    spec.write_bytes(b"# Edited elsewhere\r\n")
    stale = run_client.put(
        "/api/projects/demo/spec",
        json={"content": "mine"},
        headers=auth(token, **{"If-Match": first}),
    )
    assert stale.status_code == 412
    body = error(stale)
    assert body["code"] == "edit_conflict"
    assert body["etag"] == etag(spec)
    assert body["current"] == {"content": "# Edited elsewhere\r\n"}
    assert spec.read_bytes() == b"# Edited elsewhere\r\n"

    saved = run_client.put(
        "/api/projects/demo/spec",
        json={"content": "# Mine\r\nkept as is\n"},
        headers=auth(token, **{"If-Match": body["etag"]}),
    )
    assert saved.status_code == 200
    assert spec.read_bytes() == b"# Mine\r\nkept as is\n"
    assert saved.headers["ETag"] == etag(spec)


def test_settings_edit_with_etags(
    run_client: TestClient, token: str, run_project: Path, projects_dir: Path, git_repo: Path
) -> None:
    run_git(git_repo, "branch", "trunk")
    run_git(git_repo, "branch", "release")
    path = run_project / "project.yaml"
    got = run_client.get("/api/projects/demo/settings", headers=auth(token))
    first, settings = got.headers["ETag"], got.json()["settings"]
    assert first == etag(path)
    assert settings["name"] == "demo"

    # Unchanged settings write the same bytes.
    same = run_client.put(
        "/api/projects/demo/settings",
        json={"settings": settings},
        headers=auth(token, **{"If-Match": first}),
    )
    assert (same.status_code, same.headers["ETag"]) == (200, first)

    missing = run_client.put(
        "/api/projects/demo/settings", json={"settings": settings}, headers=auth(token)
    )
    assert missing.status_code == 428

    project = load_project("demo", projects_dir=projects_dir)
    project.default_branch = "trunk"
    save_project(project, projects_dir=projects_dir)
    on_disk = path.read_bytes()
    stale = run_client.put(
        "/api/projects/demo/settings",
        json={"settings": settings},
        headers=auth(token, **{"If-Match": first}),
    )
    assert stale.status_code == 412
    assert error(stale)["etag"] == etag(path)
    assert error(stale)["current"]["settings"]["default_branch"] == "trunk"  # type: ignore[index]
    assert path.read_bytes() == on_disk

    invalid = run_client.put(
        "/api/projects/demo/settings",
        json={"settings": {**settings, "nonsense": 1}},
        headers=auth(token, **{"If-Match": etag(path)}),
    )
    assert (invalid.status_code, error(invalid)["code"]) == (422, "validation_error")
    assert path.read_bytes() == on_disk

    changed = {**settings, "default_branch": "release"}
    saved = run_client.put(
        "/api/projects/demo/settings",
        json={"settings": changed},
        headers=auth(token, **{"If-Match": etag(path)}),
    )
    assert saved.status_code == 200
    assert saved.headers["ETag"] == etag(path)
    assert load_project("demo", projects_dir=projects_dir).default_branch == "release"


def try_command(client: TestClient, token: str | None, command: str, gate: str = "lint") -> object:
    headers = auth(token) if token else {}
    body = {"gate": gate, "command": command}
    return client.post("/api/projects/demo/commands/test", json=body, headers=headers)


@pytest.mark.integration
def test_try_a_passing_and_a_failing_command(run_client: TestClient, token: str) -> None:
    passed = try_command(run_client, token, fake_tool_cmd("pass"))
    assert passed.status_code == 200  # type: ignore[attr-defined]
    body = passed.json()  # type: ignore[attr-defined]
    assert (body["status"], body["exit_code"], body["timeout_s"]) == ("passed", 0, 90.0)
    assert "3 passed" in body["output"]

    failed = try_command(run_client, token, fake_tool_cmd("lint-error")).json()  # type: ignore[attr-defined]
    assert (failed["status"], failed["exit_code"]) == ("failed", 1)
    assert "Name 'x' is not defined" in failed["output"]

    missing = try_command(run_client, token, "no-such-program-xyz --flag").json()  # type: ignore[attr-defined]
    assert missing["status"] == "error"
    assert "not found on PATH" in missing["output"]


@pytest.mark.integration
def test_try_a_command_that_times_out(
    run_client: TestClient, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(projects_router, "COMMAND_TEST_TIMEOUT_S", 0.5)
    body = try_command(run_client, token, fake_tool_cmd("sleep")).json()  # type: ignore[attr-defined]
    assert (body["status"], body["exit_code"]) == ("timed_out", None)


@pytest.mark.integration
def test_try_a_command_runs_in_the_repo_without_a_shell(
    run_client: TestClient,
    token: str,
    git_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, dict[str, object]]] = []
    real_popen = subprocess.Popen

    def recording_popen(args: object, **kwargs: object) -> object:
        calls.append((args, kwargs))
        return real_popen(args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(subprocess, "Popen", recording_popen)
    marker = tmp_path / "marker"
    refused = try_command(run_client, token, f"{fake_tool_cmd('pass')} && touch {marker}")
    assert refused.status_code == 422  # type: ignore[attr-defined]
    assert error(refused)["field"] == "command"
    assert calls == []

    ran = try_command(run_client, token, fake_tool_cmd("marker", "made.txt"), gate="install")
    assert ran.json()["status"] == "passed"  # type: ignore[attr-defined]
    (args, kwargs) = calls[0]
    assert isinstance(args, list)
    assert kwargs.get("shell", False) is False
    assert Path(str(kwargs["cwd"])).resolve() == git_repo.resolve()
    assert (git_repo / "made.txt").read_text(encoding="utf-8") == "ran"
    assert not marker.exists()


def test_try_a_command_needs_the_token_and_a_project(run_client: TestClient, token: str) -> None:
    assert try_command(run_client, None, "just lint").status_code == 401  # type: ignore[attr-defined]
    body = {"gate": "lint", "command": "just lint"}
    missing = run_client.post("/api/projects/nope/commands/test", json=body, headers=auth(token))
    assert missing.status_code == 404
    bad_gate = try_command(run_client, token, "just lint", gate="deploy")
    assert error(bad_gate)["field"] == "gate"


def test_an_invalid_project_yaml_is_listed_with_its_first_problem(
    run_client: TestClient, token: str, run_project: Path, projects_dir: Path
) -> None:
    other = projects_dir / "zeta"
    other.mkdir()
    settings = (run_project / "project.yaml").read_text(encoding="utf-8")
    (other / "project.yaml").write_text(
        settings.replace("name: demo", "name: zeta") + "unknown_key: 1\n", encoding="utf-8"
    )
    listed = run_client.get("/api/projects", headers=auth(token)).json()
    assert [project["name"] for project in listed] == ["demo", "zeta"]
    assert listed[0]["settings_error"] is None  # the other project still loads
    problem = listed[1]["settings_error"]
    assert problem["file"] == str(other / "project.yaml")
    assert problem["field"] == "unknown_key"
    assert problem["message"] == "unknown key"
    assert listed[1]["run_state"] == "idle"

    detail = run_client.get("/api/projects/zeta", headers=auth(token))
    assert detail.status_code == 200
    assert detail.json()["settings_error"] == problem
    assert detail.json()["repo"] is None

    (other / "project.yaml").write_text("", encoding="utf-8")
    empty = run_client.get("/api/projects/zeta", headers=auth(token)).json()["settings_error"]
    assert (empty["field"], empty["message"]) == (None, "the file is empty")


def test_summary_sums_usage_and_reports_the_latest_activity(
    run_client: TestClient, token: str, run_project: Path
) -> None:
    from spoolhq.services.runs import AttemptKind, EventKind

    log = run_client.app.state.runs.open(run_project).run_log  # type: ignore[attr-defined]
    priced = log.start_attempt(log.start_run("T01").id, AttemptKind.INITIAL)
    log.record_usage(priced.id, 1000, 500, 2_500_000)
    run = log.start_run("T02")
    log.record_usage(log.start_attempt(run.id, AttemptKind.INITIAL).id, 150, 50)
    log.append_event(run.id, EventKind.RUN_PHASE, {"phase": "gates", "text": "T02 · gates"})

    summary = run_client.get("/api/projects", headers=auth(token)).json()[0]
    assert summary["usage"] == {"tokens": 200, "cost_usd": 2.5}
    assert summary["last_activity"] == log.events_since(0)[-1].ts
    assert summary["run"]["ticket_id"] == "T02"
    assert summary["run_step"] == "gates"
