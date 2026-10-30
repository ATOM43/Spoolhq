import os
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from spoolhq.cli import app
from tests.conftest import fixture_contract, make_git_template, make_template, run_git

runner = CliRunner()


def test_init_then_validate(projects_dir: Path, git_repo: Path) -> None:
    result = runner.invoke(app, ["init", "demo", "--repo", str(git_repo)])
    assert result.exit_code == 0, result.output
    folder = projects_dir / "demo"
    assert f"Created project 'demo' at {folder}" in result.output
    assert "has no PROGRESS.md, DECISIONS.md, CLAUDE.md" in result.output
    assert f"Next: write your spec in {folder / 'CONTEXT.md'}" in result.output

    validate = runner.invoke(app, ["project", "validate", "demo"])
    assert validate.exit_code == 0, validate.output
    assert validate.output == "valid\n"


def test_init_with_branch_and_remote(projects_dir: Path, git_repo: Path) -> None:
    remote = "git@github.com:ATOM43/spoolhq.git"
    result = runner.invoke(
        app, ["init", "demo", "--repo", str(git_repo), "--branch", "main", "--remote", remote]
    )
    assert result.exit_code == 0, result.output
    assert f"remote: {remote}" in (projects_dir / "demo" / "project.yaml").read_text("utf-8")


def test_init_reports_every_problem(projects_dir: Path, tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["init", "../x", "--repo", str(tmp_path / "nope"), "--remote", "https://example.com"]
    )
    assert result.exit_code == 1
    lines = result.output.splitlines()
    assert lines[0].startswith("error: name: must be 1-63 lowercase")
    assert lines[1].startswith("error: repo: path does not exist")
    assert lines[2] == "error: git.remote: not a GitHub URL"
    assert not projects_dir.exists()


def test_init_existing_folder(projects_dir: Path, git_repo: Path) -> None:
    (projects_dir / "demo").mkdir(parents=True)
    result = runner.invoke(app, ["init", "demo", "--repo", str(git_repo)])
    assert result.exit_code == 1
    assert "error: project folder already exists" in result.output


def test_validate_prints_every_error(projects_dir: Path, git_repo: Path) -> None:
    folder = projects_dir / "demo"
    folder.mkdir(parents=True)
    (folder / "project.yaml").write_text(
        "name: demo\nrepo: " + str(git_repo).replace("\\", "/") + "\ncommands:\n  lint: x\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["project", "validate", "demo"])
    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "project.yaml: commands.install: field required",
        "project.yaml: commands.test: field required",
    ]


def test_validate_missing_project(projects_dir: Path) -> None:
    result = runner.invoke(app, ["project", "validate", "nope"])
    assert result.exit_code == 1
    assert f"no project 'nope' in {projects_dir}" in result.output


@pytest.mark.usefixtures("git_identity")
def test_init_with_a_local_template(projects_dir: Path, tmp_path: Path) -> None:
    template = make_template(tmp_path / "tpl")
    repo = tmp_path / "new"
    result = runner.invoke(app, ["init", "demo", "--repo", str(repo), "--template", str(template)])
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0] == f"template: {template.resolve()}"
    assert lines[1] == f"Generated {repo.resolve()} (one commit on main)"
    assert "Created project 'demo'" in result.output
    assert "check the commands" not in result.output
    assert run_git(repo, "log", "--format=%s").strip() == "chore: apply template fixture"


@pytest.mark.usefixtures("git_identity")
def test_init_with_a_git_template_prints_the_commit_first(
    projects_dir: Path, tmp_path: Path
) -> None:
    url, commit = make_git_template(tmp_path)
    repo = tmp_path / "new"
    result = runner.invoke(
        app,
        ["init", "demo", "--repo", str(repo), "--template", url, "--template-ref", "main"],
    )
    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[0] == f"template: {url} at commit {commit}"
    yaml = (projects_dir / "demo" / "project.yaml").read_text(encoding="utf-8")
    assert f"ref: {commit}" in yaml


@pytest.mark.integration
@pytest.mark.usefixtures("git_identity")
@pytest.mark.parametrize("local", [False, True], ids=["url", "local-repo"])
def test_init_with_a_git_template_runs_no_global_git_hooks(tmp_path: Path, local: bool) -> None:
    # A subprocess, because Copier's git (plumbum) reads the environment once at import,
    # so a monkeypatched GIT_CONFIG_GLOBAL would never reach it.
    url, commit = make_git_template(tmp_path)
    if local:  # the work tree the bare repo was cloned from: a local git repository
        url = (tmp_path / "template-work").as_posix()
    hooks = tmp_path / "global-hooks"
    hooks.mkdir()
    marker = tmp_path / "hook-ran"
    hook = hooks / "post-checkout"
    hook.write_text(f'#!/bin/sh\necho ran > "{marker.as_posix()}"\n', encoding="utf-8")
    hook.chmod(0o755)
    config = tmp_path / "gitconfig-hooks"
    config.write_text(f"[core]\n\thooksPath = {hooks.as_posix()}\n", encoding="utf-8")
    repo = tmp_path / "new"
    result = subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [sys.executable, "-m", "spoolhq", "init", "demo", "--repo", str(repo), "--template", url],
        env={**os.environ, "GIT_CONFIG_GLOBAL": str(config)},
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines()[0] == f"template: {url} at commit {commit}"
    assert (repo / "README.md").is_file()
    assert not marker.exists()


def test_init_with_a_bad_template_creates_nothing(projects_dir: Path, tmp_path: Path) -> None:
    template = make_template(tmp_path / "x", contract=fixture_contract(test=None))
    repo = tmp_path / "new"
    result = runner.invoke(app, ["init", "demo", "--repo", str(repo), "--template", str(template)])
    assert result.exit_code == 1
    assert (
        "error: template 'x': spoolhq-template.yaml has no 'test' command; "
        "every template must declare install, lint and test"
    ) in result.output
    assert not repo.exists()
    assert not (projects_dir / "demo").exists()


def test_init_template_ref_needs_a_template(projects_dir: Path, git_repo: Path) -> None:
    result = runner.invoke(app, ["init", "demo", "--repo", str(git_repo), "--template-ref", "v1"])
    assert result.exit_code == 1
    assert "error: --template-ref needs --template" in result.output
