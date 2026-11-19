"""``inspect_repo``: what an existing repo already has, read without running anything."""

import json
from pathlib import Path

import pytest

from spoolhq.services.creation import CreationError, DetectedCommands, inspect_repo
from spoolhq.services.creation.inspect import detect_commands
from tests.conftest import run_git

pytestmark = pytest.mark.usefixtures("git_identity")


def write(repo: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text, encoding="utf-8")
    return repo


JUSTFILE = """\
set shell := ["bash", "-c"]
version := "1"

install:
    uv sync

@lint target="src":
    ruff check {{target}}

test *args: install
    pytest {{args}}
"""
MAKEFILE = """\
PY ?= python
.PHONY: install lint test
install:
\tpip install -e .
lint test: install
\t$(PY) -m pytest
"""
PYPROJECT = """\
[project]
name = "x"
dependencies = ["httpx"]

[dependency-groups]
dev = ["pytest>=8", "pytest-cov"]

[tool.ruff]
line-length = 100
"""


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        (
            {"justfile": JUSTFILE},
            DetectedCommands("just install", "just lint", "just test", "justfile"),
        ),
        (
            {"Makefile": MAKEFILE},
            DetectedCommands("make install", "make lint", "make test", "Makefile"),
        ),
        (
            {"package.json": json.dumps({"scripts": {"lint": "eslint .", "test": "vitest"}})},
            DetectedCommands("npm install", "npm run lint", "npm test", "package.json"),
        ),
        (
            {
                "package.json": json.dumps({"scripts": {"test": "jest"}}),
                "pnpm-lock.yaml": "",
            },
            DetectedCommands("pnpm install", None, "pnpm test", "package.json"),
        ),
        (
            {"package.json": "{}", "yarn.lock": ""},
            DetectedCommands("yarn install", None, None, "package.json"),
        ),
        (
            {"pyproject.toml": PYPROJECT, "uv.lock": ""},
            DetectedCommands("uv sync", "uv run ruff check .", "uv run pytest", "pyproject.toml"),
        ),
        (
            {
                "pyproject.toml": '[project]\nname = "x"\ndependencies = ["pytest-cov"]\n',
                "uv.lock": "",
            },
            DetectedCommands("uv sync", None, None, "pyproject.toml"),
        ),
        ({"pyproject.toml": PYPROJECT}, DetectedCommands()),  # no uv.lock
        ({"justfile": "build:\n    cargo build\n"}, DetectedCommands()),
        ({"README.md": "# hi\n"}, DetectedCommands()),
        # Precedence: a justfile with recipes beats package.json.
        (
            {"justfile": "test:\n    pytest\n", "package.json": "{}"},
            DetectedCommands(None, None, "just test", "justfile"),
        ),
        # A justfile without matching recipes falls through.
        (
            {"justfile": "build:\n    true\n", "package.json": "{}"},
            DetectedCommands("npm install", None, None, "package.json"),
        ),
        ({"package.json": "not json"}, DetectedCommands()),
    ],
    ids=[
        "justfile",
        "makefile",
        "npm",
        "pnpm",
        "yarn",
        "uv",
        "uv-no-pytest",
        "pyproject-without-uv-lock",
        "justfile-without-recipes",
        "none",
        "justfile-first",
        "falls-through",
        "bad-json",
    ],
)
def test_detected_commands(
    tmp_path: Path, files: dict[str, str], expected: DetectedCommands
) -> None:
    assert detect_commands(write(tmp_path, files)) == expected


def test_a_symlinked_justfile_is_not_read(tmp_path: Path) -> None:
    outside = write(tmp_path / "outside", {"justfile": "test:\n    true\n"})
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "justfile").symlink_to(outside / "justfile")
    assert detect_commands(repo) == DetectedCommands()


def test_a_clean_repo(git_repo: Path) -> None:
    write(git_repo, {"justfile": JUSTFILE, "PROGRESS.md": "# Progress\n"})
    run_git(git_repo, "add", ".")
    run_git(git_repo, "commit", "--quiet", "-m", "x")
    found = inspect_repo(str(git_repo), own_folders=[])
    assert (found.branch, found.clean, found.dirty) == ("main", True, [])
    assert found.commands.source == "justfile"
    assert found.notes_missing == ["DECISIONS.md"]
    assert (found.origin, found.agent_settings) == (None, [])


def test_a_dirty_repo_lists_its_files(git_repo: Path) -> None:
    write(git_repo, {"notes.txt": "x"})
    found = inspect_repo(str(git_repo), own_folders=[])
    assert (found.clean, found.dirty) == (False, ["?? notes.txt"])
    assert found.notes_missing == ["PROGRESS.md", "DECISIONS.md"]


@pytest.mark.parametrize(
    ("url", "origin"),
    [
        ("https://github.com/o/r", "https://github.com/o/r"),
        ("git@github.com:o/r.git", "git@github.com:o/r.git"),
        ("https://gitlab.com/o/r", None),
    ],
)
def test_a_github_origin(git_repo: Path, url: str, origin: str | None) -> None:
    run_git(git_repo, "remote", "add", "origin", url)
    assert inspect_repo(str(git_repo), own_folders=[]).origin == origin


def test_agent_settings_are_listed(git_repo: Path) -> None:
    write(git_repo, {".claude/settings.json": "{}", ".mcp.json": "{}", ".codex/config.toml": ""})
    found = inspect_repo(str(git_repo), own_folders=[])
    assert found.agent_settings == [".claude/settings.json", ".codex/config.toml", ".mcp.json"]


def test_inspect_never_runs_a_command(git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import spoolhq.services.gates.runner as gates_runner

    def refuse(*_: object, **__: object) -> None:
        raise AssertionError("inspect ran a command")

    monkeypatch.setattr(gates_runner, "run_process", refuse)
    monkeypatch.setattr(gates_runner, "_run_gate", refuse)
    write(git_repo, {"justfile": JUSTFILE, "package.json": "{}", "Makefile": MAKEFILE})
    assert inspect_repo(str(git_repo), own_folders=[]).commands.source == "justfile"


@pytest.mark.parametrize(
    ("path", "message"),
    [
        ("relative/path", "Use an absolute path"),
        ("HOME", "Choose a folder inside your home folder, not the home folder itself"),
        ("OWN", "Choose a folder outside SpoolHQ's own folders"),
        ("MISSING", "The folder doesn't exist"),
        ("PLAIN", "Not a git repository"),
    ],
)
def test_the_creation_path_refusals_apply(
    tmp_path: Path, home: Path, path: str, message: str
) -> None:
    (tmp_path / "plain").mkdir()
    raw = {
        "HOME": str(Path.home()),
        "OWN": str(home),
        "MISSING": str(tmp_path / "missing"),
        "PLAIN": str(tmp_path / "plain"),
    }.get(path, path)
    with pytest.raises(CreationError) as caught:
        inspect_repo(raw, own_folders=[home])
    assert (caught.value.field, caught.value.message) == ("repo_path", message)
