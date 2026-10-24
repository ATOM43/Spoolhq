"""Integration mechanics: bring main into a run's worktree, build the squash commit and
fast-forward the default branch to it.

All history work happens in the run's worktree; the user's main checkout only ever
sees ``merge --ff-only``, ``update-ref`` and ``tag``. Plain values in and out; the
orchestration (journal, gates, ticket status) is ``services/runloop/integration.py``.
See ``docs/integration.md``.
"""

import posixpath
import re
import tempfile
import textwrap
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path, PureWindowsPath

from spoolhq.services.git.repo import branch_sha, ensure_clean, ensure_no_operation_in_progress
from spoolhq.services.git.runner import command_error, run_git
from spoolhq.services.git.worktrees import _IDENTITY_ERRORS, IdentityError

SUBJECT_MAX = 72
BODY_WIDTH = 72
MAX_FILE_BYTES = 5 * 1024 * 1024
# Build output dropped from the squash commit: folder names, then file names.
JUNK_DIRS = (
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "*.egg-info",
    ".pnpm-store",
    ".npm",
)
JUNK_PATHS = (".yarn/cache/",)
JUNK_FILES = ("*.pyc", ".DS_Store")
# Likely secrets: the ticket is blocked for a person to look.
SECRET_DIRS = (".ssh", ".claude")
SECRET_FILES = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa*",
    "id_ed25519*",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "credentials.json",
    "*.keystore",
)
SECRET_ALLOWED = (".env.example",)
_MARKER_RE = re.compile(r"^(?:<{7}(?: .*)?|={7}|>{7}(?: .*)?)\r?$", re.MULTILINE)


@dataclass(frozen=True)
class MergeIn:
    changed: bool
    """main had commits the branch didn't; the merge is staged, not yet committed."""
    conflicts: tuple[str, ...] = ()
    """Files with conflicts; the worktree is left mid-merge with their markers."""


def _git(cwd: Path, *args: str) -> str:
    return run_git(args, cwd).check().stdout


def _matches(path: str, dirs: Sequence[str], files: Sequence[str]) -> bool:
    # Case-insensitive, since macOS and Windows file systems are.
    *folders, name = path.lower().split("/")
    return any(fnmatchcase(f, p.lower()) for f in folders for p in dirs) or any(
        fnmatchcase(name, p.lower()) for p in files
    )


def is_junk(path: str) -> bool:
    nested = f"/{path.lower()}"
    return _matches(path, JUNK_DIRS, JUNK_FILES) or any(f"/{p}" in nested for p in JUNK_PATHS)


def is_secret(path: str) -> bool:
    return path.lower().rsplit("/", 1)[-1] not in SECRET_ALLOWED and _matches(
        path, SECRET_DIRS, SECRET_FILES
    )


def _clean_line(text: str) -> str:
    """One line: whitespace and control characters become single spaces."""
    chars = (" " if c.isspace() or unicodedata.category(c) == "Cc" else c for c in text)
    return " ".join("".join(chars).split())


def commit_message(ticket_id: str, title: str, note: str | None, run_id: int) -> str:
    """``T04: <title>``, the progress note wrapped at 72, then the two trailers.

    The title is untrusted: one line, control characters removed, the subject cut to
    72 characters.
    """
    subject = f"{ticket_id}: {_clean_line(title)}"[:SUBJECT_MAX].rstrip()
    parts = [subject]
    if note and (body := _clean_line(note)):
        parts.append(textwrap.fill(body, BODY_WIDTH, break_long_words=False))
    parts.append(f"SpoolHQ-Ticket: {ticket_id}\nSpoolHQ-Run: {run_id}")
    return "\n\n".join(parts) + "\n"


# --- the worktree ---------------------------------------------------------------------


def merge_head(worktree: Path) -> bool:
    """True while a merge is in progress in ``worktree``."""
    return run_git(["rev-parse", "-q", "--verify", "MERGE_HEAD"], worktree).returncode == 0


def conflict_files(worktree: Path) -> tuple[str, ...]:
    """Files git still lists as unmerged."""
    out = _git(worktree, "diff", "--name-only", "--diff-filter=U", "-z")
    return tuple(sorted({path for path in out.split("\0") if path}))


def merge_in(worktree: Path, branch: str) -> MergeIn:
    """``git merge --no-ff --no-commit <branch>`` in the run's worktree."""
    result = run_git(["merge", "--no-ff", "--no-commit", f"refs/heads/{branch}"], worktree)
    if result.returncode != 0:
        files = conflict_files(worktree)
        if not files:
            raise command_error(result)
        return MergeIn(changed=True, conflicts=files)
    return MergeIn(changed=merge_head(worktree))


def unresolved_files(worktree: Path, conflicted: Sequence[str]) -> tuple[str, ...]:
    """After staging everything: files still unmerged, or among ``conflicted`` with a
    line that is a conflict marker (``<<<<<<<``, ``=======``, ``>>>>>>>``)."""
    _git(worktree, "add", "-A")
    out = _git(worktree, "ls-files", "-u", "-z")
    left = {entry.split("\t", 1)[1] for entry in out.split("\0") if "\t" in entry}
    for path in conflicted:
        file = worktree / path
        if file.is_file() and _MARKER_RE.search(file.read_text("utf-8", errors="replace")):
            left.add(path)
    return tuple(sorted(left))


def commit(worktree: Path, message: str) -> str:
    """Commit what is staged (concluding a merge, even with no change); the new sha.

    Hooks are disabled by ``run_git``; ``user.useConfigOnly`` refuses a guessed identity.
    """
    result = run_git(
        ["-c", "user.useConfigOnly=true", "commit", "--no-verify", "--quiet", "-m", message],
        worktree,
    )
    if result.returncode != 0:
        if any(text in result.stderr for text in _IDENTITY_ERRORS):
            raise IdentityError(
                f"git user.name/user.email not set for {worktree}; set them with git config",
                command=result.args,
                returncode=result.returncode,
            )
        raise command_error(result)
    return _git(worktree, "rev-parse", "HEAD").strip()


def conclude_merge(worktree: Path, message: str) -> str:
    _git(worktree, "add", "-A")
    return commit(worktree, message)


def start_squash(worktree: Path, main_sha: str) -> list[str]:
    """Detach HEAD at the branch tip and soft-reset it to ``main_sha``: the index holds
    the branch's tree on top of main. The branch itself doesn't move. The changed files."""
    _git(worktree, "switch", "--quiet", "--detach")
    _git(worktree, "reset", "--quiet", "--soft", main_sha)
    out = _git(worktree, "diff", "--cached", "--name-only", "--no-renames", "-z", main_sha)
    return [path for path in out.split("\0") if path]


def unstage(worktree: Path, main_sha: str, paths: Sequence[str]) -> None:
    """Put ``paths`` back to main's version in the index (the files stay on disk)."""
    with tempfile.TemporaryDirectory() as tmp:
        spec = Path(tmp) / "paths"
        spec.write_bytes("\0".join(paths).encode("utf-8"))
        _git(
            worktree,
            "--literal-pathspecs",
            "reset",
            "--quiet",
            f"--pathspec-from-file={spec}",
            "--pathspec-file-nul",
            main_sha,
        )


def stage(worktree: Path, path: str) -> None:
    _git(worktree, "--literal-pathspecs", "add", "--", path)


def too_large(worktree: Path, paths: Sequence[str]) -> tuple[str, int] | None:
    """The first added or changed file over 5 MB, with its size."""
    for path in paths:
        file = worktree / path
        if file.is_file() and not file.is_symlink() and file.stat().st_size > MAX_FILE_BYTES:
            return path, file.stat().st_size
    return None


def outside_symlinks(worktree: Path, main_sha: str) -> list[tuple[str, str]]:
    """Staged symlinks (added or changed) whose target is absolute or leaves the repo.

    Read from the index, not the disk, so it works where git checks symlinks out as
    plain files (Windows). Resolved lexically from the link's folder.
    """
    out = _git(worktree, "diff", "--cached", "--raw", "--no-renames", "-z", main_sha)
    fields = out.split("\0")
    found = []
    for meta, path in zip(fields[::2], fields[1::2], strict=False):
        parts = meta.split()
        if len(parts) < 5 or parts[1] != "120000" or parts[4] == "D":
            continue
        target = _git(worktree, "cat-file", "blob", parts[3])
        joined = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
        absolute = posixpath.isabs(target) or PureWindowsPath(target).is_absolute()
        if absolute or joined == ".." or joined.startswith("../"):
            found.append((path, target))
    return found


def restore_branch(worktree: Path, branch: str) -> None:
    """Drop any in-progress merge or squash: back on ``branch`` at its tip. Worktree only."""
    if merge_head(worktree):
        _git(worktree, "merge", "--abort")
    _git(worktree, "checkout", "--quiet", "--force", branch)


# --- the main checkout ----------------------------------------------------------------


def checked_out(repo: Path, branch: str) -> bool:
    """True if the main checkout has ``branch`` checked out."""
    result = run_git(["symbolic-ref", "-q", "HEAD"], repo)
    return result.returncode == 0 and result.stdout.strip() == f"refs/heads/{branch}"


def ensure_main_ready(repo: Path, branch: str) -> None:
    """If ``branch`` is checked out in ``repo``, it must be clean with nothing in progress.

    Raises RepoNotReadyError; reads only.
    """
    if checked_out(repo, branch):
        ensure_no_operation_in_progress(repo)
        ensure_clean(repo)


def advance(repo: Path, branch: str, new: str, old: str) -> bool:
    """Move ``branch`` from ``old`` to ``new``; False if it no longer points at ``old``.

    Checked out: clean required, then ``merge --ff-only``. Otherwise ``update-ref`` with
    ``old`` as the expected value, so a moved branch is never overwritten.
    """
    if checked_out(repo, branch):
        ensure_main_ready(repo, branch)
        if _git(repo, "rev-parse", "HEAD").strip() != old:
            return False
        result = run_git(["merge", "--ff-only", "--quiet", new], repo)
    else:
        result = run_git(["update-ref", f"refs/heads/{branch}", new, old], repo)
    if result.returncode == 0:
        return True
    if branch_sha(repo, branch) != old:
        return False
    raise command_error(result)


def tag_exists(repo: Path, tag: str) -> bool:
    return run_git(["show-ref", "--verify", "--quiet", f"refs/tags/{tag}"], repo).returncode == 0


def create_tag(repo: Path, tag: str, sha: str) -> None:
    """A lightweight tag; already there at ``sha`` is fine (recovery runs it again)."""
    if tag_exists(repo, tag) and _git(repo, "rev-parse", f"refs/tags/{tag}").strip() == sha:
        return
    _git(repo, "tag", tag, sha)


def is_ancestor(repo: Path, ancestor: str, commit_sha: str) -> bool:
    result = run_git(["merge-base", "--is-ancestor", ancestor, commit_sha], repo)
    if result.returncode in (0, 1):
        return result.returncode == 0
    raise command_error(result)
