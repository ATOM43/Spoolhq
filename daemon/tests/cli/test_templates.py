"""spool templates list|check."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from spoolhq.cli import app
from tests.conftest import fake_tool_cmd, fixture_contract, make_git_template, make_template

runner = CliRunner()


def test_list_shows_fastapi_react_with_its_description() -> None:
    result = runner.invoke(app, ["templates", "list"])
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0] == "fastapi-react"
    assert lines[1].startswith("  A FastAPI backend and a React frontend")


@pytest.mark.integration
def test_check_passes(tmp_path: Path) -> None:
    template = make_template(tmp_path / "tpl")
    result = runner.invoke(app, ["templates", "check", str(template)])
    assert result.exit_code == 0, result.output
    assert f"template: {template.resolve()}" in result.output
    for gate in ("install", "lint", "test"):
        assert f"✓ {gate}  " in result.output
    assert "template 'fixture' passes its contract" in result.output


@pytest.mark.integration
def test_check_a_git_url_prints_the_commit(tmp_path: Path) -> None:
    url, commit = make_git_template(tmp_path)
    result = runner.invoke(app, ["templates", "check", url, "--ref", "main"])
    assert result.exit_code == 0, result.output
    assert f"template: {url} at commit {commit}" in result.output


@pytest.mark.integration
def test_check_fails_with_the_gate_output(tmp_path: Path) -> None:
    template = make_template(
        tmp_path / "tpl", contract=fixture_contract(test=fake_tool_cmd("fail-test"))
    )
    result = runner.invoke(app, ["templates", "check", str(template)])
    assert result.exit_code == 1
    assert "✗ test  " in result.output
    assert "failing tests:" in result.output
    assert "template 'fixture' fails its contract" in result.output


def test_check_an_unknown_template() -> None:
    result = runner.invoke(app, ["templates", "check", "nope"])
    assert result.exit_code == 1
    assert (
        "error: unknown template 'nope'; spool templates list shows the built-in ones"
        in result.output
    )
