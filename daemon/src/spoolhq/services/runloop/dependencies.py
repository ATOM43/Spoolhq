"""New dependencies: the names a ticket adds to its manifests, for the merge policy.

Manifests are read with the standard library: ``pyproject.toml`` (project, optional
and group dependencies), ``package.json`` (``dependencies``, ``devDependencies``),
``Cargo.toml`` (``[dependencies]``, dev, build and workspace ones) and
``requirements*.txt``. A name in a manifest after the ticket but not before counts;
version changes and lockfiles don't. A manifest that doesn't parse has no names.
"""

import json
import re
import tomllib
from collections.abc import Iterable
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

from spoolhq.services.git import ChangedFile, run_git

MANIFESTS = ("pyproject.toml", "package.json", "Cargo.toml", "requirements*.txt")
_REQUIREMENT = re.compile(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:[\[<>=!~;@ ]|$)")


def _python_name(requirement: Any) -> str | None:
    match = _REQUIREMENT.match(requirement) if isinstance(requirement, str) else None
    return re.sub(r"[-_.]+", "-", match.group(1)).lower() if match else None


def _keys(*tables: Any) -> set[str]:
    return {key for table in tables if isinstance(table, dict) for key in table}


def _requirements(*lists: Any) -> set[str]:
    names = (_python_name(item) for items in lists if isinstance(items, list) for item in items)
    return {name for name in names if name}


def manifest_names(name: str, text: str) -> set[str]:
    """The dependency names declared in the manifest file ``name`` (its base name)."""
    try:
        if name == "package.json":
            data = json.loads(text)
            return _keys(data.get("dependencies"), data.get("devDependencies"))
        if name.endswith(".txt"):
            lines = (line.split("#", 1)[0] for line in text.splitlines())
            return _requirements([line for line in lines if not line.lstrip().startswith("-")])
        data = tomllib.loads(text)
    except (ValueError, AttributeError):
        return set()
    if name == "Cargo.toml":
        workspace = data.get("workspace")
        return _keys(
            data.get("dependencies"),
            data.get("dev-dependencies"),
            data.get("build-dependencies"),
            workspace.get("dependencies") if isinstance(workspace, dict) else None,
        )
    project = data.get("project")
    project = project if isinstance(project, dict) else {}
    optional = project.get("optional-dependencies")
    groups = data.get("dependency-groups")
    return _requirements(
        project.get("dependencies"),
        *(optional.values() if isinstance(optional, dict) else ()),
        *(groups.values() if isinstance(groups, dict) else ()),
    )


def _show(worktree: Path, revision: str) -> str:
    shown = run_git(("show", revision), worktree)
    return shown.stdout if shown.returncode == 0 else ""


def added_dependencies(worktree: Path, base: str, changes: Iterable[ChangedFile]) -> list[str]:
    """The names the staged index adds to a manifest against ``base``, sorted."""
    added: set[str] = set()
    for change in changes:
        name = change.path.rsplit("/", 1)[-1]
        if not any(fnmatchcase(name, pattern) for pattern in MANIFESTS):
            continue
        before = manifest_names(name, _show(worktree, f"{base}:{change.old_path or change.path}"))
        added |= manifest_names(name, _show(worktree, f":{change.path}")) - before
    return sorted(added)
