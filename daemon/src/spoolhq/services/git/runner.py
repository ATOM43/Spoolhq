"""Running git: one function, ``run_git``, through which every git call goes.

git is called with an argument list, never a shell string, from the folder it works
on (``cwd``), with an environment that never prompts, takes no optional locks and
prints messages in the C locale so they can be matched. Values that come from users
or agents (ticket titles, commit messages, paths) are always separate arguments.
"""

import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TIMEOUT_S = 60.0
MIN_GIT_VERSION = (2, 36)
STDERR_LINES = 20

# Set before every subcommand: paths are printed as they are (not octal-escaped), and a
# repository's fsmonitor hook never starts a daemon on SpoolHQ's behalf.
GLOBAL_OPTIONS = ("-c", "core.quotepath=off", "-c", "core.fsmonitor=false")
ENV_OVERRIDES = {
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_OPTIONAL_LOCKS": "0",
    "LC_ALL": "C",
    "LANGUAGE": "C",
}
# Variables that point git at another repository, index or work tree. Set by git hooks
# (a test run from a pre-commit hook gets GIT_INDEX_FILE); left in place, they would
# make git act on that repository instead of ``cwd``.
ENV_REMOVED = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_PREFIX",
)
# Subcommands named with their first argument in error messages: "git worktree add".
_TWO_WORD_SUBCOMMANDS = frozenset({"worktree", "stash", "remote", "submodule", "notes"})
_VERSION_RE = re.compile(r"git version (\d+)\.(\d+)(?:\.(\d+))?\S*")


class GitError(Exception):
    """git is missing, too old, or a git command failed.

    For a failed command, ``command`` is its arguments (without ``git``), ``returncode``
    its exit code and ``stderr`` the last lines of its error output.
    """

    def __init__(
        self,
        message: str,
        *,
        command: Sequence[str] = (),
        returncode: int | None = None,
        stderr: str = "",
    ) -> None:
        super().__init__(message)
        self.command = tuple(command)
        self.returncode = returncode
        self.stderr = stderr


@dataclass(frozen=True)
class GitResult:
    args: tuple[str, ...]
    """The arguments after ``git`` (without the ``-c`` options run_git adds)."""
    returncode: int
    stdout: str
    stderr: str

    def check(self) -> "GitResult":
        """Return the result, or raise GitError if the command failed."""
        if self.returncode != 0:
            raise command_error(self)
        return self


def subcommand(args: Sequence[str]) -> str:
    """The subcommand as it is named in messages: ``worktree add``, ``commit``."""
    args = list(args)
    while len(args) >= 2 and args[0] == "-c":
        args = args[2:]
    if not args:
        return ""
    if args[0] in _TWO_WORD_SUBCOMMANDS and len(args) > 1 and not args[1].startswith("-"):
        return f"{args[0]} {args[1]}"
    return args[0]


def trim_stderr(stderr: str, lines: int = STDERR_LINES) -> str:
    return "\n".join(stderr.strip().splitlines()[-lines:])


def command_error(result: GitResult) -> GitError:
    stderr = trim_stderr(result.stderr)
    message = f"git {subcommand(result.args)} failed (exit {result.returncode})"
    if stderr:
        message += f": {stderr}"
    return GitError(message, command=result.args, returncode=result.returncode, stderr=stderr)


_git_path: str | None = None


def git_executable() -> str:
    """The git program, found on PATH once and remembered."""
    global _git_path
    if _git_path is None:
        found = shutil.which("git")
        if found is None:
            raise GitError("git not found on PATH")
        _git_path = found
    return _git_path


def git_env() -> dict[str, str]:
    env = dict(os.environ)
    for name in ENV_REMOVED:
        env.pop(name, None)
    env.update(ENV_OVERRIDES)
    return env


def run_git(args: Sequence[str], cwd: Path, *, timeout: float = DEFAULT_TIMEOUT_S) -> GitResult:
    """Run ``git <args>`` in ``cwd`` and return its result, whatever the exit code.

    Raises GitError if git is not on PATH, cannot start in ``cwd`` (a missing folder)
    or does not finish within ``timeout`` seconds. Call ``.check()`` on the result to
    raise on a non-zero exit too.
    """
    arguments = tuple(args)
    command = [git_executable(), *GLOBAL_OPTIONS, *arguments]
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argument list, no shell
            command,
            cwd=cwd,
            env=git_env(),
            # Nothing to read: git never waits on the daemon's terminal.
            stdin=subprocess.DEVNULL,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitError(
            f"git {subcommand(arguments)} did not finish within {timeout:g} s",
            command=arguments,
        ) from exc
    except OSError as exc:
        raise GitError(
            f"cannot run git {subcommand(arguments)} in {cwd}: {exc.strerror or exc}",
            command=arguments,
        ) from exc
    return GitResult(
        args=arguments,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def neutral_cwd() -> Path:
    """A folder to run git commands that need no repository (``--version``)."""
    return Path(tempfile.gettempdir())


def parse_git_version(output: str) -> tuple[int, int, int]:
    match = _VERSION_RE.search(output)
    if match is None:
        raise GitError(f"cannot read the git version from {output.strip()!r}")
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch or 0)


def check_git_version() -> tuple[int, int, int]:
    """Return git's version, raising GitError if it is older than 2.36.

    2.36 is the first version with ``git worktree list --porcelain -z``.
    """
    output = run_git(["--version"], neutral_cwd()).check().stdout
    version = parse_git_version(output)
    if version[:2] < MIN_GIT_VERSION:
        found = output.strip().removeprefix("git version ").split()[0]
        required = ".".join(str(part) for part in MIN_GIT_VERSION)
        raise GitError(f"git {required} or newer is required (found {found})")
    return version
