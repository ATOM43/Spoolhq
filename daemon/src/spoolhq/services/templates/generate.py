"""Rendering a template with Copier, without trust, and the first commit.

SpoolHQ never passes Copier's ``unsafe``/trust and gives it empty settings, so the
user's Copier trust list can't apply either: ``_tasks``, ``_migrations`` and
``_jinja_extensions`` are refused before Copier starts, and Copier's own check refuses
any it would run (for example ones pulled in with ``!include``).
"""

import os
from collections.abc import Callable
from pathlib import Path

import copier
from copier.errors import UnsafeTemplateError
from ruamel.yaml.error import YAMLError

from spoolhq.services.git import GitError, commit_staged, remove_path, run_git
from spoolhq.services.projects import InitResult, ProjectError, init_project, project_dir
from spoolhq.services.projects.yaml_io import dump, loader
from spoolhq.services.templates.contract import CONTRACT_FILE, TemplateError, load_contract
from spoolhq.services.templates.sources import ResolvedTemplate, open_template

UNSAFE_KEYS = ("_tasks", "_migrations", "_jinja_extensions")
COPIER_FILES = ("copier.yml", "copier.yaml")


def unsafe_message(label: str) -> str:
    return f"template {label!r} needs Copier tasks or extensions, which SpoolHQ doesn't run"


def check_safe(root: Path, label: str) -> None:
    """Refuse a template whose ``copier.yml`` declares tasks, migrations or extensions."""
    for name in COPIER_FILES:
        path = root / name
        if not path.is_file():
            continue
        try:
            documents = list(loader().load_all(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError, YAMLError) as exc:
            raise TemplateError(f"template {label!r}: cannot read {name}: {exc}") from exc
        for data in documents:
            if isinstance(data, dict) and any(data.get(key) for key in UNSAFE_KEYS):
                raise TemplateError(unsafe_message(label))


def render(template: ResolvedTemplate, dst: Path, project_name: str) -> None:
    """Copy the template into ``dst`` with its default answers and ``project_name``."""
    try:
        worker = copier.run_copy(
            template.copier_src,
            dst,
            data={"project_name": project_name},
            settings=copier.Settings(),  # no user defaults, no trusted prefixes
            exclude=[CONTRACT_FILE],
            defaults=True,
            quiet=True,
            unsafe=False,
            cleanup_on_error=False,  # the caller removes what it created
        )
    except UnsafeTemplateError as exc:
        raise TemplateError(unsafe_message(template.label)) from exc
    except Exception as exc:  # Copier raises many kinds (YAML, Jinja, git, OS errors)
        raise TemplateError(f"template {template.label!r}: Copier failed: {exc}") from exc
    if template.kind == "git":
        _record_git_source(dst / worker.answers_relpath, template)


def _record_git_source(answers: Path, template: ResolvedTemplate) -> None:
    """Point the answers file at the git URL and commit, not the temp checkout Copier
    rendered, so ``copier update`` can find the template again."""
    if not answers.is_file():
        return
    data = loader().load(answers.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return
    data["_src_path"] = template.source
    data["_commit"] = template.ref
    answers.write_text(dump(data), encoding="utf-8")


def init_repo(repo: Path, branch: str, message: str | None) -> None:
    """``git init``, stage everything and, with a ``message``, commit it.

    The commit goes through the integration commit helper: hooks and signing are
    disabled, and the user's own identity is required (nothing is written to it).
    """
    run_git(["init", "--quiet", f"--initial-branch={branch}"], repo).check()
    run_git(["add", "--all"], repo).check()
    if message is not None:
        commit_staged(repo, message)


def check_target(repo: Path) -> bool:
    """Whether ``repo`` already exists; refuses anything but a missing or empty folder."""
    if repo.is_symlink() or (repo.exists() and not repo.is_dir()):
        raise TemplateError(f"--repo must be a new or empty folder: {repo} is not a folder")
    if not repo.exists():
        return False
    with os.scandir(repo) as entries:
        if next(entries, None) is not None:
            raise TemplateError(
                f"--repo must be a new or empty folder: {repo} is not empty "
                "(spool init never generates over existing work)"
            )
    return True


def _clean_up(repo: Path, *, existed: bool) -> None:
    if not existed:
        remove_path(repo)
        return
    for child in repo.iterdir():
        remove_path(child)


def init_from_template(
    name: str,
    repo: Path,
    source: str,
    *,
    projects_dir: Path,
    ref: str | None = None,
    branch: str = "main",
    remote: str | None = None,
    on_resolved: Callable[[ResolvedTemplate], None] | None = None,
) -> InitResult:
    """Generate a new repository from a template and create its workspace.

    ``repo`` must not exist or be empty. ``on_resolved`` is called with the source and
    resolved commit before anything is generated. Any failure removes the repository
    files and the workspace (``init_project`` is all or nothing) before raising.
    """
    target = project_dir(name, projects_dir)
    if target.exists() or target.is_symlink():
        raise ProjectError(f"project folder already exists: {target}")
    repo = repo.expanduser().absolute()
    existed = check_target(repo)
    with open_template(source, ref) as template:
        if on_resolved is not None:
            on_resolved(template)
        contract = load_contract(template.root, template.label)
        check_safe(template.root, template.label)
        try:
            render(template, repo, name)
            init_repo(repo, branch, f"chore: apply template {contract.name}")
            return init_project(
                name,
                repo,
                projects_dir=projects_dir,
                branch=branch,
                remote=remote,
                commands=contract.commands.gates(),
                template={"name": contract.name, "source": template.source, "ref": template.ref},
                template_description=contract.description,
            )
        except (TemplateError, ProjectError, GitError, OSError) as exc:
            generated = repo.is_dir() and any(repo.iterdir())
            _clean_up(repo, existed=existed)
            if not generated:
                raise
            raise TemplateError(f"{exc}\nremoved what was generated in {repo}") from exc
        except BaseException:
            _clean_up(repo, existed=existed)
            raise
