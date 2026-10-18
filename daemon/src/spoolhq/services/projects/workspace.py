"""Project workspaces: ``<projects_dir>/<name>/`` with ``project.yaml``, ``CONTEXT.md``,
``tickets/`` and ``runs/``.

Code-facing notes (``PROGRESS.md``, ``DECISIONS.md``, ``CLAUDE.md``) live in the
project's repository, not here, because agents read them alongside the code.
"""

import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from ruamel.yaml.comments import CommentedMap

from spoolhq.services.projects import yaml_io
from spoolhq.services.projects.errors import (
    FILE_NAME,
    ProjectError,
    ProjectValidationError,
    format_errors,
)
from spoolhq.services.projects.model import FOLDER_NAME_CONTEXT, SLUG_RE, SLUG_RULE, Project

CONTEXT_FILE = "CONTEXT.md"
WORKSPACE_DIRS = ("tickets", "runs")
REPO_NOTES = ("PROGRESS.md", "DECISIONS.md", "CLAUDE.md")
PLACEHOLDER_COMMANDS = {"install": "just install", "lint": "just lint", "test": "just test"}

YAML_HEADER = "SpoolHQ project settings. Reference: docs/project-yaml.md in the SpoolHQ repo."
COMMANDS_COMMENT = (
    "Placeholders: check that these install, lint and test your repo before the first run."
)

CONTEXT_TEMPLATE = """\
# {name}

The spec for this project. SpoolHQ's planner reads this file to draft the tickets.

## Objective

What to build, and why, in a few sentences.

## Background

What exists already, who it is for, and anything the reader needs to know first.

## Requirements

- What it must do.
- Constraints: stack, platforms, performance, security.

## Deliverables

- What is handed over when the work is done (code, docs, tests, releases).
"""


@dataclass(frozen=True)
class InitResult:
    project: Project
    path: Path
    missing_notes: list[str]
    """Code-facing notes the repository does not have (SpoolHQ never writes them)."""


def project_dir(name: str, projects_dir: Path) -> Path:
    """The workspace folder for ``name``, refusing names that are not slugs."""
    if not SLUG_RE.fullmatch(name):
        raise ProjectError(f"invalid project name {name!r}: {SLUG_RULE}")
    return projects_dir / name


def list_workspaces(projects_dir: Path) -> list[Path]:
    """Every project workspace in ``projects_dir``, sorted by name.

    A workspace is a folder with a slug name and a ``project.yaml``; staging folders
    left by an interrupted ``init_project`` and stray files are skipped.
    """
    if not projects_dir.is_dir():
        return []
    return sorted(
        (
            path
            for path in projects_dir.iterdir()
            if SLUG_RE.fullmatch(path.name) and path.is_dir() and (path / FILE_NAME).is_file()
        ),
        key=lambda path: path.name,
    )


def _validate(data: Any, *, folder_name: str | None, prefix: str | None) -> Project:
    if data is None:
        raise ProjectValidationError([f"{FILE_NAME}: the file is empty"])
    if not isinstance(data, Mapping):
        raise ProjectValidationError([f"{FILE_NAME}: expected a mapping of settings"])
    context = {FOLDER_NAME_CONTEXT: folder_name} if folder_name is not None else None
    try:
        return Project.model_validate(yaml_io.to_plain(data), context=context)
    except ValidationError as exc:
        raise ProjectValidationError(format_errors(exc, Project, prefix=prefix)) from exc


def load_project(name: str, *, projects_dir: Path) -> Project:
    """Load and validate ``<projects_dir>/<name>/project.yaml``.

    Raises ProjectValidationError listing every problem, or ProjectError when the
    project or its file cannot be read.
    """
    folder = project_dir(name, projects_dir)
    if not folder.is_dir():
        raise ProjectError(f"no project {name!r} in {projects_dir}")
    data = yaml_io.read(folder / FILE_NAME)
    return _validate(data, folder_name=name, prefix=FILE_NAME)


def save_project(project: Project, *, projects_dir: Path) -> Path:
    """Write ``project`` to its ``project.yaml``, keeping the user's comments.

    Only values that changed are rewritten; settings the user left out stay out.
    """
    folder = project_dir(project.name, projects_dir)
    if not folder.is_dir():
        raise ProjectError(f"no project {project.name!r} in {projects_dir}")
    # model_copy(update=...) skips validation, so check the values before writing them.
    _validate(project.model_dump(), folder_name=project.name, prefix=FILE_NAME)

    path = folder / FILE_NAME
    doc = yaml_io.read(path) if path.exists() else None
    if not isinstance(doc, CommentedMap):
        doc = CommentedMap()
    yaml_io.merge(doc, project.model_dump(mode="json", exclude_unset=True))
    yaml_io.write_atomic(path, yaml_io.dump(doc))
    return path


def _initial_yaml(project: Project) -> str:
    doc = yaml_io.to_node(project.model_dump(mode="json", exclude_none=True))
    doc.yaml_set_start_comment(YAML_HEADER)
    doc.yaml_set_comment_before_after_key("commands", before=COMMANDS_COMMENT)
    return yaml_io.dump(doc)


def _populate(folder: Path, project: Project) -> None:
    (folder / FILE_NAME).write_text(_initial_yaml(project), encoding="utf-8", newline="\n")
    (folder / CONTEXT_FILE).write_text(
        CONTEXT_TEMPLATE.format(name=project.name), encoding="utf-8", newline="\n"
    )
    for name in WORKSPACE_DIRS:
        (folder / name).mkdir()


def init_project(
    name: str,
    repo: Path,
    *,
    projects_dir: Path,
    branch: str = "main",
    remote: str | None = None,
) -> InitResult:
    """Create the workspace for a new project on an existing git repository.

    The name, repo, branch and remote are checked first; nothing is created if any is
    invalid. The workspace is built in a temp folder next to the target and renamed
    into place, so a failure leaves nothing behind. The repository is never modified.
    """
    data: dict[str, Any] = {
        "name": name,
        "repo": str(repo.expanduser().resolve()),
        "default_branch": branch,
        "commands": dict(PLACEHOLDER_COMMANDS),
    }
    if remote is not None:
        data["git"] = {"remote": remote}
    project = _validate(data, folder_name=None, prefix=None)

    target = project_dir(project.name, projects_dir)
    if target.exists() or target.is_symlink():
        raise ProjectError(f"project folder already exists: {target}")

    projects_dir.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{project.name}.", suffix=".tmp", dir=projects_dir))
    try:
        _populate(staging, project)
        if target.exists():
            raise ProjectError(f"project folder already exists: {target}")
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    missing = [note for note in REPO_NOTES if not (project.repo_path / note).exists()]
    return InitResult(project=project, path=target, missing_notes=missing)
