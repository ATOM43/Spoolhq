"""Read-only checks on a project's main repository.

None of these changes the repository. ``ensure_clean`` and
``ensure_no_operation_in_progress`` guard every new worktree: SpoolHQ starts work only
from a repository with nothing uncommitted and no rebase or merge half done.
"""

from pathlib import Path

from spoolhq.services.git.runner import GitError, command_error, run_git

MAX_LISTED_CHANGES = 20

# git-path name -> the operation it means, checked in this order.
_OPERATION_PATHS = (
    ("rebase-merge", "rebase"),
    ("rebase-apply", "rebase"),
    ("MERGE_HEAD", "merge"),
    ("CHERRY_PICK_HEAD", "cherry-pick"),
    ("REVERT_HEAD", "revert"),
)


class RepoNotReadyError(GitError):
    """The main repository is not in a state SpoolHQ can start work from."""


class DirtyRepoError(RepoNotReadyError):
    """The repository has uncommitted changes or untracked files."""


class OperationInProgressError(RepoNotReadyError):
    """A rebase, merge, cherry-pick or revert is in progress."""


class MissingBranchError(GitError):
    """The project's default branch does not exist."""


def is_work_tree(repo: Path) -> bool:
    """True if ``repo`` is inside a git work tree (not a bare repository)."""
    result = run_git(["rev-parse", "--is-inside-work-tree"], repo)
    return result.returncode == 0 and result.stdout.strip() == "true"


def branch_sha(repo: Path, branch: str) -> str | None:
    """The commit of local branch ``branch``, or None if there is no such branch."""
    result = run_git(["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}^{{commit}}"], repo)
    if result.returncode == 0:
        return result.stdout.strip()
    if result.returncode == 1:
        return None
    raise command_error(result)


def is_branch_name(repo: Path, name: str) -> bool:
    """True if ``name`` is a valid branch name, not a revision such as ``main~1``."""
    result = run_git(["check-ref-format", "--branch", name], repo)
    # check-ref-format expands @{-1}; only a name that is itself valid counts.
    return result.returncode == 0 and result.stdout.strip() == name


def has_local_branch(repo: Path, branch: str) -> bool:
    """True if ``repo`` has the local branch ``branch``.

    Raises GitError when git fails (a corrupt ref store), instead of "not found".
    """
    result = run_git(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], repo)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise command_error(result)


def default_branch_sha(repo: Path, branch: str) -> str:
    """The commit the default branch points at; MissingBranchError if it doesn't exist."""
    sha = branch_sha(repo, branch)
    if sha is None:
        raise MissingBranchError(f"default branch {branch!r} not found in {repo}")
    return sha


def status_entries(repo: Path) -> list[str]:
    """``git status`` entries (``" M src/a.py"``, ``"?? notes.txt"``); ignored files excluded."""
    output = (
        run_git(["status", "--porcelain=v1", "-z", "--untracked-files=normal"], repo).check().stdout
    )
    fields = output.split("\0")
    entries: list[str] = []
    index = 0
    while index < len(fields):
        field = fields[index]
        index += 1
        if not field:
            continue
        code, path = field[:2], field[3:]
        if code[0] in "RC" and index < len(fields):
            # A rename or copy is followed by its original path.
            path = f"{fields[index]} -> {path}"
            index += 1
        entries.append(f"{code} {path}")
    return entries


def ensure_clean(repo: Path) -> None:
    """Raise DirtyRepoError if ``repo`` has tracked, staged or untracked (not ignored) changes."""
    entries = status_entries(repo)
    if not entries:
        return
    lines = [f"  {entry}" for entry in entries[:MAX_LISTED_CHANGES]]
    if len(entries) > MAX_LISTED_CHANGES:
        lines.append(f"  … and {len(entries) - MAX_LISTED_CHANGES} more")
    raise DirtyRepoError(
        f"repo {repo} has uncommitted changes; commit or stash them first:\n" + "\n".join(lines)
    )


def operation_in_progress(repo: Path) -> str | None:
    """``rebase``, ``merge``, ``cherry-pick`` or ``revert`` if one is in progress, else None."""
    args: list[str] = ["rev-parse"]
    for name, _ in _OPERATION_PATHS:
        args += ["--git-path", name]
    paths = run_git(args, repo).check().stdout.splitlines()
    for (_, operation), path in zip(_OPERATION_PATHS, paths, strict=True):
        if (repo / path).exists():
            return operation
    return None


def ensure_no_operation_in_progress(repo: Path) -> None:
    """Raise OperationInProgressError naming a rebase, merge, cherry-pick or revert."""
    operation = operation_in_progress(repo)
    if operation is not None:
        raise OperationInProgressError(
            f"repo {repo}: a {operation} is in progress; finish or abort it first"
        )
