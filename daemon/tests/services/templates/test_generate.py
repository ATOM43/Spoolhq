"""services/templates/generate.py: spool init --template's service."""

from pathlib import Path
from typing import Any

import pytest
from copier.errors import UnsafeTemplateError

from spoolhq.services.projects import (
    InitResult,
    ProjectError,
    load_project,
    template_description,
)
from spoolhq.services.templates import TemplateError, init_from_template, unsafe_message
from tests.conftest import fixture_contract, make_git_template, make_template, run_git

pytestmark = pytest.mark.usefixtures("git_identity")


def init(source: str | Path, repo: Path, projects_dir: Path, **kwargs: Any) -> InitResult:
    return init_from_template("demo", repo, str(source), projects_dir=projects_dir, **kwargs)


def test_a_local_template(tmp_path: Path, projects_dir: Path) -> None:
    template = make_template(tmp_path / "tpl")
    repo = tmp_path / "new"
    seen = []
    result = init(template, repo, projects_dir, on_resolved=seen.append)

    assert [t.label for t in seen] == ["tpl"]
    assert (repo / "README.md").read_text(encoding="utf-8") == "# demo\n"
    assert not (repo / "spoolhq-template.yaml").exists()
    assert "project_name: demo" in (repo / ".copier-answers.yml").read_text(encoding="utf-8")
    log = run_git(repo, "log", "--format=%s", "main").splitlines()
    assert log == ["chore: apply template fixture"]
    tracked = run_git(repo, "ls-files").split()
    assert ".copier-answers.yml" in tracked
    assert run_git(repo, "status", "--porcelain") == ""

    project = load_project("demo", projects_dir=projects_dir)
    assert project.commands.model_dump() == {
        name: getattr(result.project.commands, name) for name in ("install", "lint", "test")
    }
    assert "fake_tool.py" in project.commands.test
    assert project.template is not None
    assert project.template.model_dump() == {
        "name": "fixture",
        "source": str(template.resolve()),
        "ref": None,
    }
    assert template_description("demo", projects_dir=projects_dir) == (
        "A fixture template for tests."
    )
    yaml = (projects_dir / "demo" / "project.yaml").read_text(encoding="utf-8")
    assert "From the template's spoolhq-template.yaml." in yaml


def test_a_git_url_template_records_the_commit(tmp_path: Path, projects_dir: Path) -> None:
    url, commit = make_git_template(tmp_path)
    init(url, tmp_path / "new", projects_dir)
    project = load_project("demo", projects_dir=projects_dir)
    assert project.template is not None
    assert (project.template.source, project.template.ref) == (url, commit)
    answers = (tmp_path / "new" / ".copier-answers.yml").read_text(encoding="utf-8")
    assert f"_commit: {commit[:7]}" in answers or commit in answers


def test_an_empty_existing_folder_is_used(tmp_path: Path, projects_dir: Path) -> None:
    repo = tmp_path / "empty"
    repo.mkdir()
    init(make_template(tmp_path / "tpl"), repo, projects_dir)
    assert (repo / "README.md").is_file()


def test_a_template_without_a_test_command_is_rejected(tmp_path: Path, projects_dir: Path) -> None:
    template = make_template(tmp_path / "x", contract=fixture_contract(test=None))
    repo = tmp_path / "new"
    with pytest.raises(TemplateError) as info:
        init(template, repo, projects_dir)
    assert str(info.value) == (
        "template 'x': spoolhq-template.yaml has no 'test' command; "
        "every template must declare install, lint and test"
    )
    assert not repo.exists()
    assert not (projects_dir / "demo").exists()


@pytest.mark.parametrize("key", ["_tasks", "_migrations", "_jinja_extensions"])
def test_unsafe_features_are_refused(tmp_path: Path, projects_dir: Path, key: str) -> None:
    marker = tmp_path / "marker"
    value = {
        "_tasks": f"[{str(marker.as_posix())!r}]",
        "_migrations": "[{version: v1, command: x}]",
        "_jinja_extensions": "[jinja2.ext.debug]",
    }[key]
    copier_yml = f"{key}: {value}\nproject_name: {{type: str, default: x}}\n"
    template = make_template(tmp_path / "x", copier_yml=copier_yml)
    repo = tmp_path / "new"
    with pytest.raises(TemplateError) as info:
        init(template, repo, projects_dir)
    assert str(info.value) == unsafe_message("x")
    assert str(info.value) == (
        "template 'x' needs Copier tasks or extensions, which SpoolHQ doesn't run"
    )
    assert not repo.exists()
    assert not marker.exists()


def test_tasks_from_an_include_are_refused_by_copier_and_never_run(
    tmp_path: Path, projects_dir: Path
) -> None:
    # Our own check reads only copier.yml; Copier's check (no trust) catches the rest.
    marker = tmp_path / "marker"
    task = f"touch {marker.as_posix()}"
    copier_yml = "---\n!include extra.yml\n---\nproject_name: {type: str, default: x}\n"
    template = make_template(
        tmp_path / "x",
        copier_yml=copier_yml,
        files={"extra.yml": f"_tasks: [{task!r}]\n"},
    )
    repo = tmp_path / "new"
    with pytest.raises(TemplateError, match="needs Copier tasks or extensions") as info:
        init(template, repo, projects_dir)
    assert isinstance(info.value.__cause__, UnsafeTemplateError)
    assert not marker.exists()
    assert not repo.exists()


def test_the_users_copier_trust_list_is_ignored(
    tmp_path: Path, projects_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    template = tmp_path / "x"
    settings = tmp_path / "copier-settings.yml"
    settings.write_text(f"trust: [{template.as_posix()!r}]\n", encoding="utf-8")
    monkeypatch.setenv("COPIER_SETTINGS_PATH", str(settings))
    marker = tmp_path / "marker"
    copier_yml = "---\n!include extra.yml\n---\nproject_name: {type: str, default: x}\n"
    make_template(
        template,
        copier_yml=copier_yml,
        files={"extra.yml": f"_tasks: [{f'touch {marker.as_posix()}'!r}]\n"},
    )
    with pytest.raises(TemplateError, match="needs Copier tasks or extensions") as info:
        init(template, tmp_path / "new", projects_dir)
    assert isinstance(info.value.__cause__, UnsafeTemplateError)
    assert not marker.exists()


def test_a_non_empty_folder_is_refused_and_untouched(tmp_path: Path, projects_dir: Path) -> None:
    repo = tmp_path / "work"
    repo.mkdir()
    (repo / "notes.txt").write_text("mine", encoding="utf-8")
    with pytest.raises(TemplateError, match="is not empty"):
        init(make_template(tmp_path / "tpl"), repo, projects_dir)
    assert [p.name for p in repo.iterdir()] == ["notes.txt"]
    assert (repo / "notes.txt").read_text(encoding="utf-8") == "mine"
    assert not (projects_dir / "demo").exists()


def test_a_file_as_repo_is_refused(tmp_path: Path, projects_dir: Path) -> None:
    repo = tmp_path / "file"
    repo.write_text("x", encoding="utf-8")
    with pytest.raises(TemplateError, match="is not a folder"):
        init(make_template(tmp_path / "tpl"), repo, projects_dir)


def test_an_existing_workspace_is_refused_first(tmp_path: Path, projects_dir: Path) -> None:
    (projects_dir / "demo").mkdir(parents=True)
    repo = tmp_path / "new"
    with pytest.raises(ProjectError, match="project folder already exists"):
        init(make_template(tmp_path / "tpl"), repo, projects_dir)
    assert not repo.exists()


@pytest.mark.usefixtures("isolated_git")
def test_a_failed_commit_removes_the_repo_and_workspace(
    tmp_path: Path, projects_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for kind in ("AUTHOR", "COMMITTER"):  # no identity: the first commit fails
        monkeypatch.delenv(f"GIT_{kind}_NAME")
        monkeypatch.delenv(f"GIT_{kind}_EMAIL")
    repo = tmp_path / "new"
    with pytest.raises(TemplateError) as info:
        init(make_template(tmp_path / "tpl"), repo, projects_dir)
    assert "git user.name/user.email not set" in str(info.value)
    assert f"removed what was generated in {repo}" in str(info.value)
    assert not repo.exists()
    assert not (projects_dir / "demo").exists()


def test_a_failed_workspace_empties_an_existing_folder(tmp_path: Path, projects_dir: Path) -> None:
    repo = tmp_path / "empty"
    repo.mkdir()
    with pytest.raises(TemplateError) as info:
        init(make_template(tmp_path / "tpl"), repo, projects_dir, remote="not a url")
    assert "git.remote: not a GitHub URL" in str(info.value)
    assert repo.is_dir() and list(repo.iterdir()) == []
    assert not (projects_dir / "demo").exists()


def test_a_copier_failure_is_reported(tmp_path: Path, projects_dir: Path) -> None:
    template = make_template(tmp_path / "x", files={"bad.txt.jinja": "{{ unclosed\n"})
    repo = tmp_path / "new"
    with pytest.raises(TemplateError, match="template 'x': Copier failed"):
        init(template, repo, projects_dir)
    assert not repo.exists()
