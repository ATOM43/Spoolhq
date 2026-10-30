"""Where a template comes from: a built-in name, a local folder or a git URL.

Built-ins ship inside the package (``spoolhq/templates/<name>/``, package data). A git
URL, or a local folder that is itself a git repository, is cloned with SpoolHQ's own
git runner (hooks and signing disabled) and checked out at the resolved commit; its
``.git`` folder is then removed, so Copier renders that plain folder and never runs git
itself (its own clone would run the user's global hooks).
"""

import re
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Literal

import spoolhq
from spoolhq.services.git import GitError, remove_path, run_git
from spoolhq.services.templates.contract import CONTRACT_FILE, TemplateError, load_contract

BUILTIN_DIR = "templates"
CLONE_TIMEOUT_S = 300.0
_URL_RE = re.compile(r"^(?:[a-z][a-z0-9+.-]*://|[\w.-]+@[\w.-]+:|gh:|gl:)", re.IGNORECASE)


@dataclass(frozen=True)
class ResolvedTemplate:
    kind: Literal["builtin", "local", "git"]
    label: str
    """The name used in messages: the built-in name, the folder or repository name."""
    source: str
    """What ``project.yaml`` records as ``template.source``."""
    root: Path
    """A local folder with the template's files, to read the contract from."""
    copier_src: str
    ref: str | None
    """What ``project.yaml`` records as ``template.ref``."""


def builtin_root() -> Path:
    return Path(str(resources.files(spoolhq).joinpath(BUILTIN_DIR)))


def builtin_names() -> list[str]:
    root = builtin_root()
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if (p / CONTRACT_FILE).is_file())


def builtin_descriptions() -> list[tuple[str, str]]:
    """Each built-in template's name and description, by name."""
    return [
        (name, load_contract(builtin_root() / name, name).description) for name in builtin_names()
    ]


def is_git_url(source: str) -> bool:
    return bool(_URL_RE.match(source)) or source.rstrip("/\\").endswith(".git")


def _is_path(source: str) -> bool:
    return "/" in source or "\\" in source or source.startswith((".", "~"))


def _git(args: list[str], cwd: Path, *, remote: bool = False) -> str:
    return run_git(args, cwd, timeout=CLONE_TIMEOUT_S, remote=remote).check().stdout.strip()


def _label(source: str) -> str:
    name = re.split(r"[/\\:]", source.rstrip("/\\"))[-1]
    return name.removesuffix(".git") or source


@contextmanager
def _clone(url: str, ref: str | None) -> Iterator[ResolvedTemplate]:
    work = Path(tempfile.mkdtemp(prefix="spoolhq-template-"))
    try:
        clone = work / "template"
        label = _label(url)
        try:
            _git(["clone", "--quiet", "--no-checkout", "--", url, str(clone)], work, remote=True)
            target = ref if ref is not None else "HEAD"
            commit = _git(["rev-parse", "--verify", "--quiet", f"{target}^{{commit}}"], clone)
            _git(["checkout", "--quiet", "--detach", commit], clone)
        except GitError as exc:
            what = f"ref {ref!r}" if ref is not None else "the repository"
            raise TemplateError(f"template {label!r}: cannot fetch {what}: {exc}") from exc
        remove_path(clone / ".git")
        yield ResolvedTemplate(
            kind="git",
            label=label,
            source=url,
            root=clone,
            copier_src=str(clone),
            ref=commit,
        )
    finally:
        remove_path(work)


def _local(folder: Path) -> ResolvedTemplate:
    if not folder.is_dir():
        raise TemplateError(f"template folder not found: {folder}")
    return ResolvedTemplate(
        kind="local",
        label=folder.name,
        source=str(folder),
        root=folder,
        copier_src=str(folder),
        ref=None,
    )


@contextmanager
def open_template(source: str, ref: str | None = None) -> Iterator[ResolvedTemplate]:
    """Resolve ``source``; a git clone is removed when the block ends."""
    if ref is not None and (not ref.strip() or ref.startswith("-")):
        raise TemplateError(f"invalid --template-ref {ref!r}")
    if is_git_url(source):
        with _clone(source, ref) as resolved:
            yield resolved
        return
    if _is_path(source):
        folder = Path(source).expanduser().resolve()
        if (folder / ".git").exists():
            # Copier would clone a git work tree itself, running the user's global hooks.
            with _clone(str(folder), ref) as resolved:
                yield resolved
            return
        if ref is not None:
            raise TemplateError("--template-ref only applies to a git template")
        yield _local(folder)
        return
    if ref is not None:
        raise TemplateError("--template-ref only applies to a git template")
    if source not in builtin_names():
        raise TemplateError(
            f"unknown template {source!r}; spool templates list shows the built-in ones"
        )
    folder = builtin_root() / source
    yield ResolvedTemplate(
        kind="builtin",
        label=source,
        source=source,
        root=folder,
        copier_src=str(folder),
        ref=spoolhq.__version__,
    )
