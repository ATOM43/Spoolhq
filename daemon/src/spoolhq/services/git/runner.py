"""Running git: one function, ``run_git``, through which every git call goes.

git is called with an argument list, never a shell string, from the folder it works
on (``cwd``), with an environment that never prompts, takes no optional locks and
prints messages in the C locale so they can be matched. Values that come from users
or agents (ticket titles, commit messages, paths) are always separate arguments.
Repository hooks never run and nothing is signed (see ``hook_and_signing_options``).

Inside the daemon only one git call runs per repository at a time (see ``repo_lock``):
on Windows a git call that reads ``.git/config`` while another rewrites it fails with
"Permission denied". Calls that fail that way because another process held the config
are retried on Windows (see ``CONFIG_RETRY_DELAYS_S``).
"""

import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from spoolhq.core.config import disabled_hooks_path, ensure_home

logger = logging.getLogger(__name__)

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
# For remote calls: ssh fails at once instead of asking for a passphrase nobody sees.
SSH_BATCH_COMMAND = "ssh -o BatchMode=yes"
# Subcommands named with their first argument in error messages: "git worktree add".
_TWO_WORD_SUBCOMMANDS = frozenset({"worktree", "stash", "remote", "submodule", "notes"})
# Windows only: pauses before the 2nd and 3rd try of a call that couldn't read or lock
# the config another process was writing. A failed lock means git changed nothing.
CONFIG_RETRY_DELAYS_S = (0.1, 0.3)
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


_ssh_warned = False


def remote_env(env: dict[str, str], cwd: Path) -> dict[str, str]:
    """``env`` with ``GIT_SSH_COMMAND`` set to batch mode, unless the user chose their own
    ssh command (``GIT_SSH_COMMAND``, ``GIT_SSH`` or ``core.sshCommand``): theirs is kept,
    with one warning per process that a passphrase prompt could hang until the timeout."""
    global _ssh_warned
    own = any(env.get(name) for name in ("GIT_SSH_COMMAND", "GIT_SSH"))
    if not own:
        own = run_git(["config", "--get", "core.sshCommand"], cwd).returncode == 0
    if not own:
        return {**env, "GIT_SSH_COMMAND": SSH_BATCH_COMMAND}
    if not _ssh_warned:
        _ssh_warned = True
        logger.warning(
            "your own ssh command is set (GIT_SSH_COMMAND, GIT_SSH or core.sshCommand); "
            "a passphrase prompt could hang a git push or fetch until the timeout"
        )
    return env


def disabled_hooks_dir() -> Path:
    """The empty folder git is told to look in for hooks: ``<home>/hooks-disabled/``.

    Created if missing. Raises GitError if anything is in it, since git would run it as
    a hook; checked on every call because the folder could be written to at any time.
    """
    ensure_home()  # mode 0700, like every other entry point into the home folder
    path = disabled_hooks_path()
    path.mkdir(mode=0o700, exist_ok=True)
    with os.scandir(path) as entries:
        if next(entries, None) is not None:
            raise GitError(f"{path} must be empty; SpoolHQ uses it to disable git hooks")
    return path


def hook_and_signing_options() -> tuple[str, ...]:
    """``-c`` options that stop repository hooks and commit/tag signing.

    Command-line ``-c`` wins over repository, global and system config, so a hooks
    folder the agent can edit (``core.hooksPath=.githooks``) or a user's
    ``commit.gpgsign=true`` has no effect on SpoolHQ's own git calls.
    """
    return (
        "-c",
        f"core.hooksPath={disabled_hooks_dir()}",
        "-c",
        "commit.gpgsign=false",
        "-c",
        "tag.gpgsign=false",
        "-c",
        "tag.forceSignAnnotated=false",
    )


def run_git(
    args: Sequence[str],
    cwd: Path,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
    remote: bool = False,
) -> GitResult:
    """Run ``git <args>`` in ``cwd`` and return its result, whatever the exit code.

    ``remote`` marks a call that talks to another machine (fetch, push, clone): ssh then
    runs in batch mode (see ``remote_env``).

    Raises GitError if git is not on PATH, cannot start in ``cwd`` (a missing folder),
    does not finish within ``timeout`` seconds, or the disabled-hooks folder is not
    empty. Call ``.check()`` on the result to raise on a non-zero exit too.
    """
    arguments = tuple(args)
    command = [git_executable(), *GLOBAL_OPTIONS, *hook_and_signing_options(), *arguments]
    env = git_env()
    if remote:
        env = remote_env(env, cwd)
    with repo_lock(cwd):
        completed = _spawn(command, cwd, env, timeout, arguments)
    for delay in CONFIG_RETRY_DELAYS_S:
        if sys.platform != "win32" or not config_busy(completed.returncode, completed.stderr):
            break
        logger.warning(f"git config busy; retrying git {subcommand(arguments)}")
        time.sleep(delay)
        with repo_lock(cwd):
            completed = _spawn(command, cwd, env, timeout, arguments)
    return GitResult(
        args=arguments,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _spawn(
    command: list[str], cwd: Path, env: dict[str, str], timeout: float, arguments: tuple[str, ...]
) -> "subprocess.CompletedProcess[str]":
    try:
        return subprocess.run(  # noqa: S603 - fixed argument list, no shell
            command,
            cwd=cwd,
            env=env,
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


def config_busy(returncode: int, stderr: str) -> bool:
    """True if git failed because it couldn't read or lock ``.git/config``."""
    if returncode == 0:
        return False
    for line in stderr.splitlines():
        if "could not lock config file" in line:
            return True
        if ("unable to access" in line or "Permission denied" in line) and "config" in line:
            return True
    return False


_registry_lock = threading.Lock()
_common_dirs: dict[Path, Path] = {}
_repo_locks: dict[Path, threading.Lock] = {}


def common_dir(cwd: Path) -> Path:
    """git's common dir for ``cwd`` (shared by a repository and its worktrees), cached.

    Outside a repository, or if git can't tell, ``cwd`` itself (not cached, since a
    repository may be created there later).
    """
    with _registry_lock:
        cached = _common_dirs.get(cwd)
    if cached is not None:
        return cached
    try:
        found = subprocess.run(  # noqa: S603 - fixed argument list, no shell
            [git_executable(), *GLOBAL_OPTIONS, "rev-parse", "--git-common-dir"],
            cwd=cwd,
            env=git_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=DEFAULT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return cwd.absolute()
    if found.returncode != 0 or not found.stdout.strip():
        return cwd.absolute()
    # shortcut: cached per path for the process's life; a folder that later belongs to
    # another repository keeps the old lock. Clear the entry if SpoolHQ ever reuses paths.
    resolved = (cwd / found.stdout.strip()).resolve()
    with _registry_lock:
        _common_dirs[cwd] = resolved
    return resolved


def repo_lock(cwd: Path) -> threading.Lock:
    """The in-process lock held while git runs in ``cwd``'s repository."""
    key = common_dir(cwd)
    with _registry_lock:
        return _repo_locks.setdefault(key, threading.Lock())


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
