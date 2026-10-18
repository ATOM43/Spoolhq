from pathlib import Path

from typer.testing import CliRunner

from spoolhq.cli import app

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
