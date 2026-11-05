"""Rendering a template with Copier, without trust, and the first commit.

SpoolHQ never passes Copier's ``unsafe``/trust and gives it empty settings, so the
user's Copier trust list can't apply either: ``_tasks``, ``_migrations`` and
``_jinja_extensions`` are refused before Copier starts, and Copier's own check refuses
any it would run (for example ones pulled in with ``!include``).
"""

from pathlib import Path

import copier
from copier.errors import UnsafeTemplateError
from ruamel.yaml.error import YAMLError

from spoolhq.services.git import commit_staged, run_git
from spoolhq.services.projects.yaml_io import dump, loader
from spoolhq.services.templates.contract import CONTRACT_FILE, TemplateError
from spoolhq.services.templates.sources import ResolvedTemplate

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
