"""What an existing repo already has, read before the dialog creates a project from it.

Reads files and asks git; never runs a command from the repo. Repo files are untrusted:
symlinks are skipped and each file is read up to ``MAX_READ_BYTES``.
"""

import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from spoolhq.services.agents.repo_settings import settings_files
from spoolhq.services.creation.request import CreationError, current_branch, safe_path
from spoolhq.services.git import GitError, github_repo, is_work_tree, run_git
from spoolhq.services.git.repo import status_entries

MAX_READ_BYTES = 1_000_000
NOTES = ("PROGRESS.md", "DECISIONS.md")
GATES = ("install", "lint", "test")
JUSTFILES = ("justfile", "Justfile", ".justfile")
MAKEFILES = ("GNUmakefile", "makefile", "Makefile")
# A just recipe or make target line: its name(s), then a ':' that isn't ':=' (an assignment).
_RULE_RE = re.compile(r"^@?([A-Za-z_][\w-]*)[^\n:]*:(?!=)", re.MULTILINE)
_MAKE_RE = re.compile(r"^([A-Za-z_][\w .-]*?)\s*::?(?!=)", re.MULTILINE)
_PYTEST_RE = re.compile(r"\s*pytest(?![\w.-])", re.IGNORECASE)


@dataclass(frozen=True)
class DetectedCommands:
    install: str | None = None
    lint: str | None = None
    test: str | None = None
    source: str | None = None
    """The file they came from, like ``justfile``; None when nothing was detected."""


@dataclass(frozen=True)
class RepoInspection:
    branch: str
    clean: bool
    dirty: list[str]
    origin: str | None
    """``origin``'s URL when it is a GitHub URL."""
    commands: DetectedCommands
    agent_settings: list[str] = field(default_factory=list)
    notes_missing: list[str] = field(default_factory=list)


def _read(path: Path) -> str | None:
    if path.is_symlink() or not path.is_file():
        return None
    with path.open("rb") as file:
        return file.read(MAX_READ_BYTES).decode("utf-8", errors="replace")


def _first(repo: Path, names: tuple[str, ...]) -> tuple[str, str] | None:
    # The real names from the listing: on a case-insensitive disk, "makefile" also opens "Makefile".
    present = {entry.name for entry in repo.iterdir()}
    for name in names:
        if name in present and (text := _read(repo / name)) is not None:
            return name, text
    return None


def _from_rules(
    found: tuple[str, str] | None, rule: re.Pattern[str], tool: str
) -> DetectedCommands | None:
    if found is None:
        return None
    name, text = found
    rules = {part for match in rule.finditer(text) for part in match[1].split()}
    commands = {gate: f"{tool} {gate}" for gate in GATES if gate in rules}
    return DetectedCommands(**commands, source=name) if commands else None


def _from_package_json(repo: Path) -> DetectedCommands | None:
    text = _read(repo / "package.json")
    if text is None:
        return None
    try:
        scripts = json.loads(text).get("scripts") or {}
    except (ValueError, AttributeError):
        return None
    if not isinstance(scripts, dict):
        scripts = {}
    pm = "pnpm" if (repo / "pnpm-lock.yaml").is_file() else "npm"
    if pm == "npm" and (repo / "yarn.lock").is_file():
        pm = "yarn"
    return DetectedCommands(
        install=f"{pm} install",
        lint=f"{pm} run lint" if "lint" in scripts else None,
        test=f"{pm} test" if "test" in scripts else None,
        source="package.json",
    )


def _dependencies(data: dict[str, object]) -> list[str]:
    """Every dependency string in a pyproject: project, optional, groups and uv's dev."""
    project, tool = data.get("project"), data.get("tool")
    lists: list[object] = []
    if isinstance(project, dict):
        lists.append(project.get("dependencies"))
        extras = project.get("optional-dependencies")
        lists += list(extras.values()) if isinstance(extras, dict) else []
    groups = data.get("dependency-groups")
    lists += list(groups.values()) if isinstance(groups, dict) else []
    uv = tool.get("uv") if isinstance(tool, dict) else None
    lists.append(uv.get("dev-dependencies") if isinstance(uv, dict) else None)
    items = [item for each in lists if isinstance(each, list) for item in each]
    return [item for item in items if isinstance(item, str)]


def _from_pyproject(repo: Path) -> DetectedCommands | None:
    text = _read(repo / "pyproject.toml")
    if text is None or not (repo / "uv.lock").is_file():
        return None
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return None
    tool = data.get("tool")
    ruff = (isinstance(tool, dict) and "ruff" in tool) or any(
        (repo / name).is_file() for name in ("ruff.toml", ".ruff.toml")
    )
    pytest = any(_PYTEST_RE.match(dep) for dep in _dependencies(data))
    return DetectedCommands(
        install="uv sync",
        lint="uv run ruff check ." if ruff else None,
        test="uv run pytest" if pytest else None,
        source="pyproject.toml",
    )


def detect_commands(repo: Path) -> DetectedCommands:
    """The stack commands from the first of justfile, Makefile, package.json and
    pyproject.toml (with uv.lock) that gives any; nulls when none does."""
    return (
        _from_rules(_first(repo, JUSTFILES), _RULE_RE, "just")
        or _from_rules(_first(repo, MAKEFILES), _MAKE_RE, "make")
        or _from_package_json(repo)
        or _from_pyproject(repo)
        or DetectedCommands()
    )


def _origin(repo: Path) -> str | None:
    url = run_git(["config", "--get", "remote.origin.url"], repo).stdout.strip()
    try:
        github_repo(url)
    except ValueError:
        return None
    return url


def inspect_repo(raw_path: str, *, own_folders: list[Path]) -> RepoInspection:
    """Inspect the repo at ``raw_path``; CreationError (field ``repo_path``) for a path
    ``check_request`` would refuse, except a dirty repo, which is reported."""
    repo = safe_path(raw_path, own_folders)
    if not repo.is_dir():
        raise CreationError("repo_path", "The folder doesn't exist")
    try:
        if not is_work_tree(repo):
            raise CreationError("repo_path", "Not a git repository")
        branch = current_branch(repo)
        dirty = status_entries(repo)
        origin = _origin(repo)
    except GitError as exc:
        raise CreationError("repo_path", "git couldn't read the repository") from exc
    return RepoInspection(
        branch=branch,
        clean=not dirty,
        dirty=dirty,
        origin=origin,
        commands=detect_commands(repo),
        agent_settings=settings_files(repo),
        notes_missing=[name for name in NOTES if not (repo / name).is_file()],
    )
