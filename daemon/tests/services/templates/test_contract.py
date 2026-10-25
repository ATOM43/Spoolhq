"""services/templates/contract.py: loading and validating spoolhq-template.yaml."""

from pathlib import Path

import pytest

from spoolhq.services.templates import MAX_DESCRIPTION, TemplateError, load_contract
from tests.conftest import fixture_contract


def write(folder: Path, text: str) -> Path:
    folder.mkdir(exist_ok=True)
    (folder / "spoolhq-template.yaml").write_text(text, encoding="utf-8")
    return folder


def error(folder: Path) -> str:
    with pytest.raises(TemplateError) as info:
        load_contract(folder, "x")
    return str(info.value)


def test_a_valid_contract(tmp_path: Path) -> None:
    folder = write(tmp_path / "t", fixture_contract(dev="just dev"))
    contract = load_contract(folder, "x")
    assert contract.name == "fixture"
    assert contract.description == "A fixture template for tests."
    assert contract.commands.dev == "just dev"
    assert set(contract.commands.gates()) == {"install", "lint", "test"}


def test_a_missing_file(tmp_path: Path) -> None:
    tmp_path.joinpath("t").mkdir()
    assert error(tmp_path / "t") == (
        "template 'x': no spoolhq-template.yaml at the template root; "
        "every template must have one (docs/templates.md)"
    )


@pytest.mark.parametrize("command", ["install", "lint", "test"])
def test_a_missing_command(tmp_path: Path, command: str) -> None:
    folder = write(tmp_path / "t", fixture_contract(**{command: None}))
    assert error(folder) == (
        f"template 'x': spoolhq-template.yaml has no {command!r} command; "
        "every template must declare install, lint and test"
    )


def test_shell_syntax_in_a_command(tmp_path: Path) -> None:
    folder = write(tmp_path / "t", fixture_contract(lint="ruff check && mypy"))
    assert error(folder) == (
        "template 'x': spoolhq-template.yaml: commands.lint: "
        "shell syntax isn't supported; put it in a justfile recipe"
    )


def test_a_description_over_the_limit(tmp_path: Path) -> None:
    text = fixture_contract().replace("A fixture template for tests.", "a" * (MAX_DESCRIPTION + 1))
    folder = write(tmp_path / "t", text)
    assert error(folder) == (
        "template 'x': spoolhq-template.yaml: description: "
        "must be at most 2,000 characters, got 2,001"
    )


def test_every_problem_is_listed(tmp_path: Path) -> None:
    folder = write(tmp_path / "t", "name: Not A Slug\ncommands:\n  install: ''\n  extra: x\n")
    lines = error(folder).splitlines()
    assert lines[0].startswith("template 'x': spoolhq-template.yaml: name: must be 1-63")
    assert "template 'x': spoolhq-template.yaml: description: field required" in lines
    assert "template 'x': spoolhq-template.yaml: commands.install: must not be empty" in lines
    assert any("commands.extra: unknown key" in line for line in lines)
    assert any("has no 'lint' command" in line for line in lines)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("name: [\n", "template 'x': spoolhq-template.yaml: line 2, column 1:"),
        ("- a list\n", "template 'x': spoolhq-template.yaml: expected a mapping"),
    ],
)
def test_bad_yaml(tmp_path: Path, text: str, message: str) -> None:
    assert error(write(tmp_path / "t", text)).startswith(message)
