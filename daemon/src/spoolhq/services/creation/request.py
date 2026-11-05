"""What a new project is made from, and every check made before a creation job starts.

The repo path comes from the desktop app's webview, so it is untrusted: it is resolved
and refused when it is the disk root, the home folder, inside SpoolHQ's own folders or
a symlink. Templates are only the built-in names, since a Copier template can run code.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from spoolhq.services.gates import GATE_NAMES, check_gate_command
from spoolhq.services.git import (
    DirtyRepoError,
    GitError,
    ensure_clean,
    has_local_branch,
    is_work_tree,
    run_git,
)
from spoolhq.services.projects import project_dir
from spoolhq.services.projects.model import check_github_url
from spoolhq.services.templates import builtin_names

NAME_RE = re.compile(r"[a-z][a-z0-9-]{0,39}")
NAME_RULE = "Use lowercase letters, digits and hyphens, starting with a letter"

Source = Literal["template", "existing", "empty"]
MergePreset = Literal["direct_unless_risky", "always_pr", "always_direct"]
MERGE_PRESETS: dict[str, dict[str, Any]] = {
    # The model's defaults: diff size, protected paths, review_required and needs_human.
    "direct_unless_risky": {},
    # "**" matches every path, so every ticket needs a person (a PR with a remote).
    "always_pr": {"protected_paths": ["**"]},
    # Diff size (at its maximum) and protected paths off; review_required and a
    # reviewer's needs_human still apply.
    "always_direct": {"max_diff_lines": 100_000, "protected_paths": []},
}
"""Each preset as ``project.yaml``'s ``merge_policy`` (DECISIONS 339)."""


class StackCommands(BaseModel):
    model_config = ConfigDict(extra="forbid")

    install: str | None = Field(default=None, max_length=4096)
    lint: str | None = Field(default=None, max_length=4096)
    test: str | None = Field(default=None, max_length=4096)


class CreateProject(BaseModel):
    """``POST /api/projects`` and ``spool init``: a new project and where its repo comes from."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=64)
    """``^[a-z][a-z0-9-]{0,39}$``."""
    source: Source
    repo_path: str = Field(min_length=1, max_length=4096)
    """Absolute. ``existing``: a clean git repository; otherwise a new or empty folder."""
    template: str | None = Field(default=None, max_length=200)
    """For ``template`` only: a name from ``GET /api/templates``."""
    commands: StackCommands = Field(default_factory=StackCommands)
    """Each one required unless ``source`` is ``empty``."""
    git_remote: str | None = Field(default=None, max_length=2048)
    merge_preset: MergePreset = "direct_unless_risky"
    clickup_list_id: str | None = Field(default=None, max_length=200)


class CreationError(Exception):
    """The request is refused before any job starts; ``field`` is the request field."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field
        self.message = message


@dataclass(frozen=True)
class Checked:
    """A request that passed every check."""

    request: CreateProject
    repo: Path
    """``repo_path``, resolved."""
    repo_existed: bool
    branch: str
    commands: dict[str, str]
    """The commands that are set, in gate order."""

    def settings(self) -> dict[str, Any]:
        """The ``merge_policy`` and ``tracker`` settings the request asks for."""
        extra: dict[str, Any] = {}
        if policy := MERGE_PRESETS[self.request.merge_preset]:
            extra["merge_policy"] = policy
        if self.request.clickup_list_id:
            extra["tracker"] = {"kind": "clickup", "list_id": self.request.clickup_list_id}
        return extra


def _commands(request: CreateProject) -> dict[str, str]:
    commands: dict[str, str] = {}
    for gate in GATE_NAMES:
        value = (getattr(request.commands, gate) or "").strip()
        if not value:
            if request.source != "empty":
                raise CreationError(f"commands.{gate}", f"Set the {gate} command")
            continue
        try:
            check_gate_command(value)
        except ValueError as exc:
            raise CreationError(f"commands.{gate}", str(exc)) from exc
        commands[gate] = value
    return commands


def _refuse(message: str) -> CreationError:
    return CreationError("repo_path", message)


def _safe_path(raw: str, own_folders: list[Path]) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        raise _refuse("Use an absolute path")
    if path.is_symlink():
        raise _refuse("The folder is a symlink; choose the folder it points to")
    repo = path.resolve()
    if repo == Path(repo.anchor):
        raise _refuse("Choose a folder, not the root of the disk")
    if repo == Path.home().resolve():
        raise _refuse("Choose a folder inside your home folder, not the home folder itself")
    if any(repo.is_relative_to(folder.expanduser().resolve()) for folder in own_folders):
        raise _refuse("Choose a folder outside SpoolHQ's own folders")
    return repo


def _current_branch(repo: Path) -> str:
    result = run_git(["symbolic-ref", "--quiet", "--short", "HEAD"], repo)
    branch = result.stdout.strip()
    if result.returncode != 0 or not branch:
        raise _refuse("Check out a branch first; HEAD is detached")
    if not has_local_branch(repo, branch):
        raise _refuse("The repository has no commits yet")
    return branch


def _check_existing(repo: Path) -> str:
    if not repo.is_dir():
        raise _refuse("The folder doesn't exist")
    try:
        if not is_work_tree(repo):
            raise _refuse("Not a git repository")
        ensure_clean(repo)
        return _current_branch(repo)
    except DirtyRepoError as exc:
        raise _refuse(str(exc)) from exc
    except GitError as exc:
        raise _refuse("git couldn't read the repository") from exc


def _check_new(repo: Path) -> bool:
    """Whether the (empty) folder exists already."""
    if not repo.exists():
        if not repo.parent.is_dir():
            raise _refuse("The parent folder doesn't exist")
        return False
    if not repo.is_dir():
        raise _refuse("Not a folder")
    if any(repo.iterdir()):
        raise _refuse("Choose a new or empty folder")
    return True


def check_request(
    request: CreateProject, *, projects_dir: Path, worktrees_dir: Path, home: Path
) -> Checked:
    """Every check, in field order; CreationError names the first field that fails."""
    if not NAME_RE.fullmatch(request.name):
        raise CreationError("name", NAME_RULE)
    workspace = project_dir(request.name, projects_dir)
    if workspace.exists() or workspace.is_symlink():
        raise CreationError("name", "A project with this name already exists")
    if request.source == "template":
        if request.template not in builtin_names():
            raise CreationError("template", "Choose one of the templates the app lists")
    elif request.template is not None:
        raise CreationError("template", "Only a template project takes a template")
    repo = _safe_path(request.repo_path, [projects_dir, worktrees_dir, home])
    if request.source == "existing":
        existed, branch = True, _check_existing(repo)
    else:
        existed, branch = _check_new(repo), "main"
    commands = _commands(request)
    if request.git_remote is not None:
        try:
            check_github_url(request.git_remote)
        except ValueError as exc:
            raise CreationError(
                "git_remote", "Use a GitHub URL like https://github.com/o/r"
            ) from exc
    if request.clickup_list_id is not None and not request.clickup_list_id.strip():
        raise CreationError("clickup_list_id", "Enter the ClickUp list id")
    return Checked(request, repo, existed, branch, commands)
