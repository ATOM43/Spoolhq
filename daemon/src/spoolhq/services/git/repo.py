"""Read-only checks on a local repository.

Every call is ``git -C <repo> ...`` with an argument list, never a shell string, and
none of them changes the repository.
"""

import shutil
import subprocess
from pathlib import Path

GIT_TIMEOUT_S = 30.0


class GitError(Exception):
    """git is not installed or did not answer."""


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    git = shutil.which("git")
    if git is None:
        raise GitError("git was not found on PATH")
    try:
        return subprocess.run(  # noqa: S603 - fixed argument list, no shell
            [git, "-C", str(repo), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitError(f"git did not answer within {GIT_TIMEOUT_S:.0f} s") from exc


def is_work_tree(repo: Path) -> bool:
    """True if ``repo`` is inside a git work tree (not a bare repository)."""
    result = _git(repo, "rev-parse", "--is-inside-work-tree")
    return result.returncode == 0 and result.stdout.strip() == "true"


def branch_exists(repo: Path, branch: str) -> bool:
    """True if ``repo`` has a local branch ``branch`` with at least one commit."""
    result = _git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}^{{commit}}")
    return result.returncode == 0
