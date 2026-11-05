"""services/templates/generate.py: rendering a template with Copier, without trust."""

from pathlib import Path

import pytest
from copier.errors import UnsafeTemplateError

from spoolhq.services.projects.yaml_io import parse as load_yaml
from spoolhq.services.templates import (
    TemplateError,
    check_safe,
    init_repo,
    load_contract,
    open_template,
    render,
    unsafe_message,
)
from tests.conftest import fixture_contract, make_git_template, make_template, run_git

pytestmark = pytest.mark.usefixtures("git_identity")


def generate(source: str | Path, repo: Path, ref: str | None = None) -> None:
    """What the creation job does: contract, safety check, then Copier."""
    with open_template(str(source), ref) as template:
        load_contract(template.root, template.label)
        check_safe(template.root, template.label)
        render(template, repo, "demo")


def test_a_local_template(tmp_path: Path) -> None:
    template = make_template(tmp_path / "tpl")
    repo = tmp_path / "new"
    generate(template, repo)
    init_repo(repo, "main", "chore: generate from fixture")

    assert (repo / "README.md").read_text(encoding="utf-8") == "# demo\n"
    assert not (repo / "spoolhq-template.yaml").exists()
    assert "project_name: demo" in (repo / ".copier-answers.yml").read_text(encoding="utf-8")
    assert run_git(repo, "log", "--format=%s", "main").splitlines() == [
        "chore: generate from fixture"
    ]
    assert ".copier-answers.yml" in run_git(repo, "ls-files").split()
    assert run_git(repo, "status", "--porcelain") == ""


def test_a_git_url_template_records_the_commit(tmp_path: Path) -> None:
    url, commit = make_git_template(tmp_path)
    generate(url, tmp_path / "new")
    answers = load_yaml((tmp_path / "new" / ".copier-answers.yml").read_text(encoding="utf-8"))
    # `git describe --always`: a short hash, quoted by YAML when it is all digits.
    assert commit.startswith(str(answers["_commit"]))
    assert answers["_src_path"] == url


def test_an_empty_existing_folder_is_used(tmp_path: Path) -> None:
    repo = tmp_path / "empty"
    repo.mkdir()
    generate(make_template(tmp_path / "tpl"), repo)
    assert (repo / "README.md").is_file()


def test_a_template_without_a_test_command_is_rejected(tmp_path: Path) -> None:
    template = make_template(tmp_path / "x", contract=fixture_contract(test=None))
    repo = tmp_path / "new"
    with pytest.raises(TemplateError) as info:
        generate(template, repo)
    assert str(info.value) == (
        "template 'x': spoolhq-template.yaml has no 'test' command; "
        "every template must declare install, lint and test"
    )
    assert not repo.exists()


@pytest.mark.parametrize("key", ["_tasks", "_migrations", "_jinja_extensions"])
def test_unsafe_features_are_refused(tmp_path: Path, key: str) -> None:
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
        generate(template, repo)
    assert str(info.value) == unsafe_message("x")
    assert str(info.value) == (
        "template 'x' needs Copier tasks or extensions, which SpoolHQ doesn't run"
    )
    assert not repo.exists()
    assert not marker.exists()


def test_tasks_from_an_include_are_refused_by_copier_and_never_run(
    tmp_path: Path,
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
        generate(template, repo)
    assert isinstance(info.value.__cause__, UnsafeTemplateError)
    assert not marker.exists()
    assert not repo.exists()


def test_the_users_copier_trust_list_is_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
        generate(template, tmp_path / "new")
    assert isinstance(info.value.__cause__, UnsafeTemplateError)
    assert not marker.exists()


def test_a_copier_failure_is_reported(tmp_path: Path) -> None:
    template = make_template(tmp_path / "x", files={"bad.txt.jinja": "{{ unclosed\n"})
    repo = tmp_path / "new"
    with pytest.raises(TemplateError, match="template 'x': Copier failed"):
        generate(template, repo)
    assert not repo.exists()
