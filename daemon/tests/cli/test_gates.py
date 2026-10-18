"""`spool gates run`."""

import json
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from spoolhq.cli import app
from tests.conftest import fake_tool_cmd

pytestmark = pytest.mark.integration

runner = CliRunner()


@pytest.fixture(autouse=True)
def temp_logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The command's log folder goes under the test's tmp dir."""
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))


def set_commands(workspace: Path, test_mode: str) -> dict[str, str]:
    commands = {
        "install": fake_tool_cmd("pass"),
        "lint": fake_tool_cmd("pass"),
        "test": fake_tool_cmd(test_mode),
    }
    path = workspace / "project.yaml"
    text = path.read_text(encoding="utf-8")
    for name, command in commands.items():
        text = text.replace(f"{name}: just {name}", f"{name}: {json.dumps(command)}")
    path.write_text(text, encoding="utf-8")
    return commands


def test_passing_gates_exit_0(workspace: Path, tmp_path: Path) -> None:
    commands = set_commands(workspace, "pass")

    result = runner.invoke(app, ["gates", "run", "demo", "--path", str(tmp_path)])

    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert lines[0].startswith("logs: ")
    assert Path(lines[0].removeprefix("logs: "), "test.log").is_file()
    assert len(lines) == 4
    for line, name in zip(lines[1:], ("install", "lint", "test"), strict=True):
        assert line.startswith(f"✓ {name}  {commands[name]}  ")
        assert line.endswith(" s")


def test_failing_test_exits_1_with_the_test_names(workspace: Path, tmp_path: Path) -> None:
    commands = set_commands(workspace, "fail-test")

    result = runner.invoke(app, ["gates", "run", "demo", "--path", str(tmp_path)])

    assert result.exit_code == 1
    assert f"✗ test  {commands['test']}  exit 1  " in result.stdout
    assert "FAILED tests/test_math.py::test_add - assert 2 == 3" in result.stdout
    assert result.stdout.endswith(
        "failing tests:\n  tests/test_math.py::test_add\n  tests/test_math.py::test_sub\n"
    )


def test_defaults_to_the_repository(workspace: Path, git_repo: Path) -> None:
    set_commands(workspace, "pass")
    result = runner.invoke(app, ["gates", "run", "demo"])
    assert result.exit_code == 0, result.output


def test_unknown_project_and_missing_folder(workspace: Path, tmp_path: Path) -> None:
    result = runner.invoke(app, ["gates", "run", "nope"])
    assert result.exit_code == 1
    assert result.stderr.startswith("error: no project 'nope'")

    result = runner.invoke(app, ["gates", "run", "demo", "--path", str(tmp_path / "gone")])
    assert result.exit_code == 1
    assert result.stderr == f"error: not a folder: {tmp_path / 'gone'}\n"
