"""The built-in fastapi-react template, for real: generate it, run its gates with no
agent, and check that its own lint enforces its layering (slow: installs packages)."""

import os
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from typer.testing import CliRunner

import spoolhq
from spoolhq.cli import app
from spoolhq.services.gates import gate_env, read_total
from spoolhq.services.projects import load_project
from spoolhq.services.templates import init_repo, open_template, render
from tests.conftest import run_git

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        any(shutil.which(tool) is None for tool in ("just", "uv", "pnpm")),
        reason="needs just, uv and pnpm on PATH",
    ),
]

runner = CliRunner()


def just(repo: Path, recipe: str) -> subprocess.CompletedProcess[str]:
    program = shutil.which("just")
    assert program is not None
    return subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [program, recipe],
        cwd=repo,
        env=gate_env(os.environ, platform=sys.platform),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
        check=False,
    )


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """A generated copy, installed once for the lint tests."""
    repo = tmp_path_factory.mktemp("fastapi-react") / "demo"
    with open_template("fastapi-react") as template:
        render(template, repo, "demo")
    init_repo(repo, "main", None)
    installed = just(repo, "install")
    assert installed.returncode == 0, installed.stdout + installed.stderr
    yield repo


@pytest.mark.usefixtures("git_identity")
def test_init_generates_one_commit_and_fills_the_commands(
    tmp_path: Path, projects_dir: Path
) -> None:
    repo = tmp_path / "demo"
    result = runner.invoke(
        app, ["init", "demo", "--repo", str(repo), "--template", "fastapi-react"]
    )
    assert result.exit_code == 0, result.output
    for step in ("Create workspace", "Prepare repo", "Check commands", "Initial commit"):
        assert f"passed   {step}" in result.output
    assert run_git(repo, "log", "--format=%s").splitlines() == [
        f"chore: generate from fastapi-react {spoolhq.__version__}"
    ]
    assert run_git(repo, "status", "--porcelain") == ""
    for path in ("backend/app/main.py", "frontend/src/app/main.tsx", ".copier-answers.yml"):
        assert path in run_git(repo, "ls-files")
    assert "# demo" in (repo / "README.md").read_text(encoding="utf-8")
    assert not (repo / "spoolhq-template.yaml").exists()

    project = load_project("demo", projects_dir=projects_dir)
    assert project.commands.model_dump() == {
        "install": "just install",
        "lint": "just lint",
        "test": "just test",
    }
    assert project.template is not None
    assert project.template.name == "fastapi-react"
    assert project.notes.decision_areas == ["general", "api", "data", "ui", "infra", "testing"]
    assert project.gates.coverage_report == "backend/coverage.xml"
    assert "decision_areas:" in (projects_dir / "demo" / "project.yaml").read_text("utf-8")
    assert "Feature-Sliced Design" in (projects_dir / "demo" / "TEMPLATE.md").read_text("utf-8")


def test_the_contract_check_passes_with_no_agent() -> None:
    result = runner.invoke(app, ["templates", "check", "fastapi-react"])
    assert result.exit_code == 0, result.output
    for gate in ("install", "lint", "test"):
        assert f"✓ {gate}  just {gate}" in result.output
    assert "notes:" not in result.output  # the notes check passes before any ticket
    assert "template 'fastapi-react' passes its contract" in result.output


def test_lint_catches_fastapi_in_services(generated: Path) -> None:
    bad = generated / "backend" / "app" / "services" / "items" / "web.py"
    bad.write_text(
        "from fastapi import HTTPException\n\n\n"
        "def refuse() -> None:\n    raise HTTPException(status_code=500)\n",
        encoding="utf-8",
    )
    try:
        result = just(generated, "lint")
    finally:
        bad.unlink()
    assert result.returncode != 0
    assert "services never import FastAPI or Starlette BROKEN" in result.stdout
    assert "app.services.items.web -> fastapi" in result.stdout


def test_lint_catches_a_sibling_slice_import(generated: Path) -> None:
    slice_dir = generated / "frontend" / "src" / "features" / "edit-item"
    slice_dir.mkdir()
    (slice_dir / "index.ts").write_text(
        'export { CreateItemForm as EditItemForm } from "@/features/create-item";\n',
        encoding="utf-8",
    )
    try:
        result = just(generated, "lint")
    finally:
        shutil.rmtree(slice_dir)
    assert result.returncode != 0
    assert "boundaries/dependencies" in result.stdout


def test_lint_passes_without_violations(generated: Path) -> None:
    result = just(generated, "lint")
    assert result.returncode == 0, result.stdout + result.stderr


def test_lint_catches_open_without_an_encoding(generated: Path) -> None:
    bad = generated / "backend" / "app" / "core" / "reader.py"
    bad.write_text('def read() -> str:\n    return open("x").read()\n', encoding="utf-8")
    try:
        result = just(generated, "lint")
    finally:
        bad.unlink()
    assert result.returncode != 0
    assert "unspecified-encoding" in result.stdout  # PLW1514


def test_the_test_recipe_writes_the_coverage_report(generated: Path) -> None:
    result = just(generated, "test")
    assert result.returncode == 0, result.stdout + result.stderr
    total = read_total(generated, "backend/coverage.xml")
    assert total is not None and total >= 80
    assert run_git(generated, "status", "--porcelain", "--", "backend/coverage.xml") == ""
