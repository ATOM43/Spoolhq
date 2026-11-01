"""Project, settings and spec endpoints: listing, creating, and edits with ETags."""

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from spoolhq.services.projects import load_project, save_project
from tests.conftest import run_git


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
        {"name": "demo", "done": 0, "total": 1, "run_state": "idle", "needs_you": 0}
    ]
    detail = run_client.get("/api/projects/demo", headers=auth(token)).json()
    assert detail["default_branch"] == "main"
    assert detail["invalid_tickets"] == 1
    assert detail["remote"] is None


def test_unknown_or_invalid_project_names(run_client: TestClient, token: str) -> None:
    missing = run_client.get("/api/projects/nope", headers=auth(token))
    assert missing.status_code == 404
    assert error(missing) == {"code": "not_found", "message": "no project 'nope'"}
    invalid = run_client.get("/api/projects/Not_A_Slug/spec", headers=auth(token))
    assert invalid.status_code == 422
    assert error(invalid)["code"] == "validation_error"
    assert error(invalid)["field"] == "name"


def test_create_project_like_spool_init(
    client: TestClient, token: str, git_repo: Path, projects_dir: Path
) -> None:
    body = {"name": "fresh", "repo": str(git_repo)}
    created = client.post("/api/projects", json=body, headers=auth(token))
    assert created.status_code == 201
    assert created.json()["name"] == "fresh"
    assert (projects_dir / "fresh" / "project.yaml").is_file()

    again = client.post("/api/projects", json=body, headers=auth(token))
    assert again.status_code == 409
    assert error(again)["message"].startswith("project folder already exists")
    no_template = client.post(
        "/api/projects", json={**body, "name": "x", "template_ref": "v1"}, headers=auth(token)
    )
    assert (no_template.status_code, error(no_template)["field"]) == (422, "template_ref")


def test_create_project_from_an_unknown_template(
    client: TestClient, token: str, tmp_path: Path
) -> None:
    body = {"name": "gen", "repo": str(tmp_path / "new"), "template": "no-such-template"}
    response = client.post("/api/projects", json=body, headers=auth(token))
    assert response.status_code == 409
    assert error(response)["code"] == "template_error"


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
