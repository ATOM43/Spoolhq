import os
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

import spoolhq
from spoolhq.cli import app
from spoolhq.services.projects import load_project
from tests.conftest import fake_tool_cmd, make_git_template, make_template, run_git

runner = CliRunner()
PASS = fake_tool_cmd("pass")
COMMANDS = ["--install", PASS, "--lint", PASS, "--test", PASS]

pytestmark = pytest.mark.usefixtures("git_identity")


@pytest.mark.integration
def test_init_an_existing_repo_then_validate(projects_dir: Path, git_repo: Path) -> None:
    remote = "git@github.com:ATOM43/spoolhq.git"
    result = runner.invoke(
        app, ["init", "demo", "--repo", str(git_repo), *COMMANDS, "--remote", remote]
    )
    assert result.exit_code == 0, result.output
    folder = projects_dir / "demo"
    assert result.output.splitlines()[:4] == [
        "passed   Create workspace",
        "passed   Prepare repo",
        "passed   Check commands",
        "skipped  Initial commit",
    ]
    assert f"Created project 'demo' at {folder}" in result.output
    assert "has no PROGRESS.md, DECISIONS.md, CLAUDE.md" in result.output
    assert f"Next: write your spec in {folder / 'CONTEXT.md'}" in result.output
    assert load_project("demo", projects_dir=projects_dir).git.remote == remote

    validate = runner.invoke(app, ["project", "validate", "demo"])
    assert validate.exit_code == 0, validate.output
    assert validate.output == "valid\n"


def test_init_refuses_a_bad_request_before_anything(projects_dir: Path, tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "../x", "--repo", str(tmp_path / "nope")])
    assert result.exit_code == 1
    assert result.output.startswith("error: name: Use lowercase letters, digits and hyphens")
    result = runner.invoke(app, ["init", "demo", "--repo", str(tmp_path / "nope")])
    assert result.output.startswith("error: repo_path: The folder doesn't exist")
    assert not projects_dir.exists()


def test_init_existing_folder(projects_dir: Path, git_repo: Path) -> None:
    (projects_dir / "demo").mkdir(parents=True)
    result = runner.invoke(app, ["init", "demo", "--repo", str(git_repo), *COMMANDS])
    assert result.exit_code == 1
    assert "error: name: A project with this name already exists" in result.output


@pytest.mark.integration
@pytest.mark.usefixtures("builtin_fixture")
def test_init_from_a_template_fills_its_commands(projects_dir: Path, tmp_path: Path) -> None:
    repo = tmp_path / "new"
    result = runner.invoke(app, ["init", "demo", "--repo", str(repo), "--template", "fixture"])
    assert result.exit_code == 0, result.output
    assert run_git(repo, "log", "--format=%s").strip() == (
        f"chore: generate from fixture {spoolhq.__version__}"
    )
    assert load_project("demo", projects_dir=projects_dir).commands.test == PASS


@pytest.mark.integration
def test_init_rolls_back_a_failed_step(projects_dir: Path, tmp_path: Path) -> None:
    repo = tmp_path / "new"
    args = ["init", "demo", "--repo", str(repo), "--source", "empty"]
    result = runner.invoke(app, [*args, "--test", fake_tool_cmd("fail-test")])
    assert result.exit_code == 1
    assert "error: commands.test: The test command failed" in result.output
    assert "FAILED tests/test_math.py::test_add" in result.output
    assert f"removed {repo}" in result.output
    assert not repo.exists()
    assert not projects_dir.exists()


@pytest.mark.integration
def test_init_from_a_local_folder_template(projects_dir: Path, tmp_path: Path) -> None:
    folder = make_template(tmp_path / "my-template")
    repo = tmp_path / "new"
    result = runner.invoke(app, ["init", "demo", "--repo", str(repo), "--template", str(folder)])
    assert result.exit_code == 0, result.output
    assert (repo / "README.md").read_text(encoding="utf-8") == "# demo\n"
    template = load_project("demo", projects_dir=projects_dir).template
    assert template is not None
    assert (template.name, template.source, template.ref) == (
        "fixture",
        str(folder.resolve()),
        None,
    )
    assert run_git(repo, "branch", "--show-current").strip() == "main"


@pytest.mark.integration
def test_init_from_a_git_template_at_a_ref(projects_dir: Path, tmp_path: Path) -> None:
    url, commit = make_git_template(tmp_path)
    repo = tmp_path / "new"
    args = ["init", "demo", "--repo", str(repo), "--template", url, "--template-ref", "main"]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    template = load_project("demo", projects_dir=projects_dir).template
    assert template is not None
    assert (template.source, template.ref) == (url, commit)
    assert f"_commit: {commit}" in (repo / ".copier-answers.yml").read_text(encoding="utf-8")


@pytest.mark.integration
def test_init_refuses_an_unsafe_folder_template(projects_dir: Path, tmp_path: Path) -> None:
    unsafe = "_tasks: [echo hi]\nproject_name:\n  type: str\n  default: x\n"
    folder = make_template(tmp_path / "unsafe", copier_yml=unsafe)
    repo = tmp_path / "new"
    result = runner.invoke(app, ["init", "demo", "--repo", str(repo), "--template", str(folder)])
    assert result.exit_code == 1
    assert "error: template: Couldn't generate the project" in result.output
    assert "needs Copier tasks or extensions" in result.output
    assert not repo.exists()
    assert not projects_dir.exists()


@pytest.mark.integration
def test_init_an_empty_repo_on_a_branch(projects_dir: Path, tmp_path: Path) -> None:
    repo = tmp_path / "new"
    args = ["init", "demo", "--repo", str(repo), "--source", "empty", "--branch", "dev"]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert run_git(repo, "branch", "--show-current").strip() == "dev"
    assert load_project("demo", projects_dir=projects_dir).default_branch == "dev"


def test_init_refuses_a_branch_for_an_existing_repo(projects_dir: Path, git_repo: Path) -> None:
    args = ["init", "demo", "--repo", str(git_repo), *COMMANDS, "--branch", "dev"]
    result = runner.invoke(app, args)
    assert result.exit_code == 1
    assert result.output == "error: branch: An existing repo uses its checked-out branch\n"
    result = runner.invoke(app, [*args[:-2], "--template-ref", "v1"])
    assert "error: template_ref: Only a git template takes a ref" in result.output
    assert not projects_dir.exists()


def test_init_refuses_a_bad_branch_name(projects_dir: Path, tmp_path: Path) -> None:
    args = ["init", "demo", "--repo", str(tmp_path / "n"), "--source", "empty"]
    result = runner.invoke(app, [*args, "--branch", "a..b"])
    assert result.exit_code == 1
    assert "error: branch: 'a..b' is not a valid branch name" in result.output


def test_validate_prints_every_error(projects_dir: Path, git_repo: Path) -> None:
    folder = projects_dir / "demo"
    folder.mkdir(parents=True)
    (folder / "project.yaml").write_text(
        "name: demo\nrepo: "
        + str(git_repo).replace("\\", "/")
        + "\ncommands:\n  lint: a && b\nlimits:\n  gate_retries: 99\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["project", "validate", "demo"])
    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "project.yaml: commands.lint: shell syntax isn't supported; put it in a justfile recipe",
        "project.yaml: limits.gate_retries: must be at most 10",
    ]


def test_validate_missing_project(projects_dir: Path) -> None:
    result = runner.invoke(app, ["project", "validate", "nope"])
    assert result.exit_code == 1
    assert f"no project 'nope' in {projects_dir}" in result.output


@pytest.mark.integration
@pytest.mark.usefixtures("git_identity")
@pytest.mark.parametrize("local", [False, True], ids=["url", "local-repo"])
def test_a_git_template_check_runs_no_global_git_hooks(tmp_path: Path, local: bool) -> None:
    # A subprocess, because Copier's git (plumbum) reads the environment once at import,
    # so a monkeypatched GIT_CONFIG_GLOBAL would never reach it.
    url, commit = make_git_template(tmp_path)
    shown = url
    if local:  # the work tree the bare repo was cloned from: a local git repository
        url = (tmp_path / "template-work").as_posix()
        shown = str((tmp_path / "template-work").resolve())  # a folder prints resolved
    hooks = tmp_path / "global-hooks"
    hooks.mkdir()
    marker = tmp_path / "hook-ran"
    hook = hooks / "post-checkout"
    hook.write_text(f'#!/bin/sh\necho ran > "{marker.as_posix()}"\n', encoding="utf-8")
    hook.chmod(0o755)
    config = tmp_path / "gitconfig-hooks"
    config.write_text(f"[core]\n\thooksPath = {hooks.as_posix()}\n", encoding="utf-8")
    result = subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [sys.executable, "-m", "spoolhq", "templates", "check", url],
        env={**os.environ, "GIT_CONFIG_GLOBAL": str(config)},
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines()[1] == f"template: {shown} at commit {commit}"
    assert "template 'fixture' passes its contract" in result.stdout
    assert not marker.exists()
