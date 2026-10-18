"""Worktrees: the disposable working copy each run of a ticket works in.

One worktree per run, at ``<root>/<project>/<ticket_id>``, on its own branch
``feat/<ticket_id>-<slug>`` made from the project's local default branch. When
SpoolHQ creates a branch it records the run in the main repository's config
(``branch.<branch>.spoolhq = <run_id>``); only branches carrying that marker are ever
deleted or recreated. See ``docs/git.md``.
"""

import logging
import os
import re
import shutil
import stat
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from spoolhq.core.ids import TICKET_ID_RE
from spoolhq.services.git.naming import branch_name, check_ticket_id
from spoolhq.services.git.repo import (
    branch_sha,
    default_branch_sha,
    ensure_clean,
    ensure_no_operation_in_progress,
)
from spoolhq.services.git.runner import GitError, GitResult, command_error, run_git

logger = logging.getLogger(__name__)

MARKER = "spoolhq"
# One plain folder name: no separators, never "." or "..".
_PROJECT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
_HEADS = "refs/heads/"
# What git says when a commit has no author or committer identity.
_IDENTITY_ERRORS = ("identity unknown", "auto-detection is disabled", "empty ident name")


class WorktreeExistsError(GitError):
    """The ticket already has a worktree (registered with git, or its folder exists)."""


class BranchConflictError(GitError):
    """The ticket's branch exists and SpoolHQ may not replace it."""


class IdentityError(GitError):
    """git has no user.name / user.email to commit with."""


@dataclass(frozen=True)
class Worktree:
    ticket_id: str
    branch: str
    path: Path
    base_sha: str
    """The default branch's commit the branch started from."""
    run_id: str
    """The run that created the branch (its SpoolHQ marker)."""


@dataclass(frozen=True)
class WorktreeSession(Worktree):
    """The worktree of ``WorktreeManager.session``; ``keep()`` stops its teardown."""

    _state: dict[str, bool] = field(default_factory=dict, repr=False, compare=False)

    def keep(self) -> None:
        """Leave the worktree in place when the session ends (a blocked run, for inspection)."""
        self._state["kept"] = True

    @property
    def kept(self) -> bool:
        return self._state.get("kept", False)


class WorktreeState(StrEnum):
    OK = "ok"
    MISSING_FOLDER = "missing folder"
    NOT_REGISTERED = "not registered"
    NO_MARKER = "no marker"


@dataclass(frozen=True)
class WorktreeInfo:
    """A worktree under the project's root, as git and the file system see it."""

    ticket_id: str
    path: Path
    branch: str | None
    registered: bool
    """git knows the worktree (``git worktree list``)."""
    folder_exists: bool
    has_marker: bool
    """The branch carries SpoolHQ's marker."""

    @property
    def state(self) -> WorktreeState:
        if not self.folder_exists:
            return WorktreeState.MISSING_FOLDER
        if not self.registered:
            return WorktreeState.NOT_REGISTERED
        if not self.has_marker:
            return WorktreeState.NO_MARKER
        return WorktreeState.OK


@dataclass(frozen=True)
class RegisteredWorktree:
    """One entry of ``git worktree list --porcelain -z``."""

    path: Path
    head: str | None = None
    branch: str | None = None
    """The branch checked out, without ``refs/heads/``; None when detached."""
    bare: bool = False
    detached: bool = False
    locked: bool = False
    prunable: bool = False


def parse_worktree_list(output: str) -> list[RegisteredWorktree]:
    """Parse ``git worktree list --porcelain -z``: NUL-ended lines, an empty one per entry."""
    entries: list[RegisteredWorktree] = []
    lines: list[str] = []
    for line in [*output.split("\0"), ""]:
        if line:
            lines.append(line)
            continue
        fields = {key: value for key, _, value in (item.partition(" ") for item in lines)}
        lines = []
        if "worktree" not in fields:
            continue
        branch = fields.get("branch")
        entries.append(
            RegisteredWorktree(
                path=Path(fields["worktree"]),
                head=fields.get("HEAD"),
                branch=branch.removeprefix(_HEADS) if branch else None,
                bare="bare" in fields,
                detached="detached" in fields,
                locked="locked" in fields,
                prunable="prunable" in fields,
            )
        )
    return entries


def marker_key(branch: str) -> str:
    return f"branch.{branch}.{MARKER}"


def same_path(a: Path, b: Path) -> bool:
    """True if both name the same place (symlinks resolved; case-insensitive on Windows)."""
    return _norm(a) == _norm(b)


def _norm(path: Path) -> str:
    return os.path.normcase(os.path.realpath(path))


def _clear_read_only_and_retry(func: Callable[..., object], path: str, exc: BaseException) -> None:
    """``shutil.rmtree`` error handler: make the path (and its folder) writable, retry once.

    Windows refuses to delete read-only files, and POSIX refuses to empty a read-only
    folder. A second failure propagates.
    """
    for target in (path, os.path.dirname(path)):
        try:
            mode = os.lstat(target).st_mode
            os.chmod(target, mode | stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        except OSError:
            pass
    func(path)


def remove_path(path: Path) -> None:
    """Delete a folder tree, file or symlink (never following a symlink)."""
    if path.is_symlink() or path.is_file():
        try:
            path.unlink()
        except PermissionError:
            os.chmod(path, stat.S_IWRITE)
            path.unlink()
    elif path.exists():
        shutil.rmtree(path, onexc=_clear_read_only_and_retry)


def _ticket_order(ticket_id: str) -> tuple[int, str]:
    return int(ticket_id[1:]), ticket_id


class WorktreeManager:
    """Create, commit in, list and remove a project's worktrees.

    ``repo`` is the project's main repository, ``default_branch`` the local branch new
    work starts from and ``root`` the folder holding every project's worktrees
    (``~/.spoolhq/worktrees``). Nothing outside ``<root>/<project>`` is ever deleted;
    in the main repository only ``git worktree prune``, branch creation and deletion
    and the marker config are changed.
    """

    def __init__(self, repo: Path, project: str, default_branch: str, root: Path) -> None:
        if not _PROJECT_RE.fullmatch(project):
            raise ValueError(f"invalid project name {project!r}")
        self.repo = repo
        self.project = project
        self.default_branch = default_branch
        self.root = root.expanduser().absolute()
        self.project_root = self.root / project

    # git helpers ---------------------------------------------------------------------

    def _git(self, *args: str, cwd: Path | None = None) -> GitResult:
        return run_git(args, cwd or self.repo)

    def _log(self, message: str, ticket_id: str, **extra: object) -> None:
        logger.info(message, extra={"project": self.project, "ticket_id": ticket_id, **extra})

    def path_for(self, ticket_id: str) -> Path:
        """``<root>/<project>/<ticket_id>``; ValueError for an invalid ticket id."""
        return self.project_root / check_ticket_id(ticket_id)

    def registered(self) -> list[RegisteredWorktree]:
        """Every worktree git knows for the repository, the main one first."""
        output = self._git("worktree", "list", "--porcelain", "-z").check().stdout
        return parse_worktree_list(output)

    def _entry_for(
        self, path: Path, entries: list[RegisteredWorktree] | None = None
    ) -> RegisteredWorktree | None:
        for entry in self.registered() if entries is None else entries:
            if same_path(entry.path, path):
                return entry
        return None

    def _ticket_of(self, path: Path) -> str | None:
        """The ticket id if ``path`` is ``<project_root>/<ticket_id>``, else None."""
        if TICKET_ID_RE.fullmatch(path.name) and same_path(path.parent, self.project_root):
            return path.name
        return None

    def markers(self) -> dict[str, str]:
        """Branch -> run id, for every branch carrying the SpoolHQ marker."""
        result = self._git("config", "--local", "--get-regexp", rf"^branch\..*\.{MARKER}$")
        if result.returncode == 1:
            return {}
        markers: dict[str, str] = {}
        for line in result.check().stdout.splitlines():
            key, _, value = line.partition(" ")
            branch = key.removeprefix("branch.").removesuffix(f".{MARKER}")
            if value.strip():
                markers[branch] = value.strip()
        return markers

    def marker(self, branch: str) -> str | None:
        """The run id in ``branch``'s SpoolHQ marker, or None if it has none."""
        result = self._git("config", "--local", "--get", marker_key(branch))
        if result.returncode == 1:
            return None
        value = result.check().stdout.strip()
        return value or None

    def prune(self) -> None:
        """``git worktree prune``: forget registered worktrees whose folder is gone."""
        self._git("worktree", "prune").check()

    # create, resume ------------------------------------------------------------------

    def create(self, ticket_id: str, title: str, run_id: int | str) -> Worktree:
        """Create the ticket's worktree on a new branch from the default branch.

        Refuses a repository with uncommitted changes or an operation in progress, a
        ticket that already has a worktree and a branch SpoolHQ didn't create. A stale
        SpoolHQ branch checked out nowhere is deleted and recreated. If anything fails
        after ``git worktree add``, what was created is removed again.
        """
        run = str(run_id).strip()
        if not run:
            raise ValueError("run_id must not be empty")
        path = self.path_for(ticket_id)
        branch = branch_name(ticket_id, title, cwd=self.repo)

        ensure_no_operation_in_progress(self.repo)
        ensure_clean(self.repo)
        entries = self.registered()
        if self._entry_for(path, entries) is not None or path.exists() or path.is_symlink():
            raise WorktreeExistsError(
                f"{ticket_id} already has a worktree at {path}; resume it or remove it first"
            )
        base_sha = default_branch_sha(self.repo, self.default_branch)
        self._clear_stale_branch(ticket_id, branch, entries)

        self.project_root.mkdir(parents=True, exist_ok=True)
        added = self._git("worktree", "add", "-b", branch, str(path), base_sha)
        if added.returncode != 0:
            self._undo_create(ticket_id, path, branch)
            raise command_error(added)
        try:
            self._git("config", "--local", marker_key(branch), run).check()
        except BaseException:
            self._undo_create(ticket_id, path, branch)
            raise
        self._log("created worktree", ticket_id, path=str(path), branch=branch, run_id=run)
        return Worktree(
            ticket_id=ticket_id, branch=branch, path=path, base_sha=base_sha, run_id=run
        )

    def _clear_stale_branch(
        self, ticket_id: str, branch: str, entries: list[RegisteredWorktree]
    ) -> None:
        if branch_sha(self.repo, branch) is None:
            return
        if self.marker(branch) is None:
            raise BranchConflictError(
                f"branch {branch} exists and was not created by SpoolHQ; rename or delete it"
            )
        checked_out = [entry for entry in entries if entry.branch == branch]
        if checked_out:
            raise BranchConflictError(
                f"branch {branch} is checked out at {checked_out[0].path}; "
                "remove that worktree first"
            )
        logger.info(
            f"recreating stale SpoolHQ branch {branch}",
            extra={"project": self.project, "ticket_id": ticket_id, "branch": branch},
        )
        self._git("branch", "-D", branch).check()

    def _undo_create(self, ticket_id: str, path: Path, branch: str) -> None:
        """Remove what a failed ``create`` made. The branch didn't exist before it."""
        try:
            if self._entry_for(path) is not None:
                self._git("worktree", "remove", "--force", str(path))
            remove_path(path)
            self.prune()
            if branch_sha(self.repo, branch) is not None:
                self._git("branch", "-D", branch).check()
        except (GitError, OSError) as exc:
            logger.error(
                "cannot clean up after a failed worktree create",
                extra={"project": self.project, "ticket_id": ticket_id, "error": str(exc)},
            )
        else:
            self._log("removed the worktree of a failed create", ticket_id, path=str(path))

    def resume(self, ticket_id: str) -> Worktree | None:
        """The ticket's worktree if git has it, its folder exists and its branch is marked."""
        path = self.path_for(ticket_id)
        entry = self._entry_for(path)
        if entry is None or entry.branch is None or not path.is_dir():
            return None
        run_id = self.marker(entry.branch)
        if run_id is None:
            return None
        base_sha = (
            self._git("merge-base", f"{_HEADS}{self.default_branch}", f"{_HEADS}{entry.branch}")
            .check()
            .stdout.strip()
        )
        return Worktree(
            ticket_id=ticket_id, branch=entry.branch, path=path, base_sha=base_sha, run_id=run_id
        )

    # commit --------------------------------------------------------------------------

    def commit_all(self, wt: Worktree, message: str) -> str | None:
        """Stage everything in the worktree and commit it; the new sha, or None if no change.

        Commits skip the repository's hooks (``--no-verify``): the gates are the checks.
        """
        if not message.strip():
            raise ValueError("commit message must not be empty")
        self._git("add", "-A", cwd=wt.path).check()
        staged = self._git("diff", "--cached", "--quiet", cwd=wt.path)
        if staged.returncode == 0:
            return None
        if staged.returncode != 1:
            raise command_error(staged)
        # useConfigOnly: refuse to commit as a guessed user@hostname identity.
        committed = self._git(
            "-c", "user.useConfigOnly=true", "commit", "--no-verify", "-m", message, cwd=wt.path
        )
        if committed.returncode != 0:
            if any(text in committed.stderr for text in _IDENTITY_ERRORS):
                raise IdentityError(
                    f"git user.name/user.email not set for {self.repo}; set them with git config",
                    command=committed.args,
                    returncode=committed.returncode,
                )
            raise command_error(committed)
        sha = self._git("rev-parse", "HEAD", cwd=wt.path).check().stdout.strip()
        self._log("committed", wt.ticket_id, branch=wt.branch, sha=sha)
        return sha

    # teardown ------------------------------------------------------------------------

    def teardown(self, target: Worktree | str, *, delete_branch: bool = True) -> None:
        """Remove a ticket's worktree, its folder and (if marked) its branch.

        Safe to call again: with nothing left to remove it only prunes.
        """
        ticket_id = target.ticket_id if isinstance(target, Worktree) else target
        path = self.path_for(ticket_id)
        entry = self._entry_for(path)
        branch = target.branch if isinstance(target, Worktree) else None
        if branch is None and entry is not None:
            branch = entry.branch

        if entry is not None:
            removed = self._git("worktree", "remove", "--force", str(path))
            if removed.returncode == 0:
                self._log("removed worktree", ticket_id, path=str(path))
            else:
                logger.warning(
                    "git worktree remove failed; deleting the folder",
                    extra={
                        "project": self.project,
                        "ticket_id": ticket_id,
                        "path": str(path),
                        "error": str(command_error(removed)),
                    },
                )
        if path.exists() or path.is_symlink():
            remove_path(path)
            self._log("deleted worktree folder", ticket_id, path=str(path))
        self.prune()
        self._log("pruned worktrees", ticket_id)
        if delete_branch and branch is not None:
            self._delete_marked_branch(ticket_id, branch)

    def _delete_marked_branch(self, ticket_id: str, branch: str) -> None:
        if branch == self.default_branch or branch_sha(self.repo, branch) is None:
            return
        if self.marker(branch) is None:
            self._log("kept branch without the SpoolHQ marker", ticket_id, branch=branch)
            return
        # Deleting the branch also removes its config section, marker included.
        self._git("branch", "-D", branch).check()
        self._log("deleted branch", ticket_id, branch=branch)

    @contextmanager
    def session(self, ticket_id: str, title: str, run_id: int | str) -> Iterator[WorktreeSession]:
        """Create a worktree and tear it down when the block ends, unless ``keep()`` was called.

        Teardown runs on a normal exit and on any exception. A teardown failure after
        an exception is logged, so the original exception is the one raised.
        """
        wt = self.create(ticket_id, title, run_id)
        session = WorktreeSession(wt.ticket_id, wt.branch, wt.path, wt.base_sha, wt.run_id)
        try:
            yield session
        except BaseException:
            if not session.kept:
                try:
                    self.teardown(session)
                except (GitError, OSError) as exc:
                    logger.error(
                        "cannot tear down the worktree",
                        extra={"project": self.project, "ticket_id": ticket_id, "error": str(exc)},
                    )
            raise
        if not session.kept:
            self.teardown(session)

    # listing -------------------------------------------------------------------------

    def list_worktrees(self) -> list[WorktreeInfo]:
        """Every worktree under ``<root>/<project>``: registered ones and unknown folders.

        Only entries named like a ticket (``T04``) directly under the project's root
        count. Read-only.
        """
        markers = self.markers()
        infos: dict[str, WorktreeInfo] = {}
        for entry in self.registered():
            ticket_id = self._ticket_of(entry.path)
            if ticket_id is None:
                continue
            path = self.project_root / ticket_id
            infos[ticket_id] = WorktreeInfo(
                ticket_id=ticket_id,
                path=path,
                branch=entry.branch,
                registered=True,
                folder_exists=path.is_dir(),
                has_marker=entry.branch is not None and entry.branch in markers,
            )
        if self.project_root.is_dir():
            for child in self.project_root.iterdir():
                if child.name in infos or not TICKET_ID_RE.fullmatch(child.name):
                    continue
                infos[child.name] = WorktreeInfo(
                    ticket_id=child.name,
                    path=child,
                    branch=None,
                    registered=False,
                    folder_exists=True,
                    has_marker=False,
                )
        return [infos[ticket_id] for ticket_id in sorted(infos, key=_ticket_order)]
