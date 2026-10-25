"""Remote mechanics: fetch the default branch, compare it with the local one, push.

Every call goes through ``run_git`` with the user's own credential helper or SSH agent;
SpoolHQ never puts credentials into a URL, argv or git config, and hooks stay disabled.
A fetched branch is stored as ``refs/spoolhq/remote/<branch>`` in the main repository,
so neither the user's remotes nor their remote-tracking branches change. Pushes are
plain pushes: never ``--force``. Plain values in and out. See ``docs/github.md``.
"""

import re
from dataclasses import replace
from enum import StrEnum
from pathlib import Path

from spoolhq.services.git.runner import command_error, run_git

NETWORK_TIMEOUT_S = 300.0
LISTED_COMMITS = 20
REMOTE_REF_PREFIX = "refs/spoolhq/remote/"

# GitHub's rules: an owner is 1-39 letters, digits or hyphens, not starting with a
# hyphen; a repository is 1-100 letters, digits, '.', '_' or '-', not starting with
# '-' or '.'.
_GITHUB_OWNER = r"(?P<owner>[A-Za-z0-9][A-Za-z0-9-]{0,38})"
_GITHUB_REPO = r"(?P<repo>[A-Za-z0-9_][A-Za-z0-9._-]{0,99}?)"
GITHUB_HTTPS_RE = re.compile(rf"https://github\.com/{_GITHUB_OWNER}/{_GITHUB_REPO}(?:\.git)?")
GITHUB_SSH_RE = re.compile(rf"git@github\.com:{_GITHUB_OWNER}/{_GITHUB_REPO}\.git")
# `git push --porcelain` flags a ref git refused because the remote has moved on.
_MOVED_RE = re.compile(r"\[rejected\] \((?:fetch first|non-fast-forward)\)")


class PushResult(StrEnum):
    PUSHED = "pushed"
    MOVED = "moved"
    """Rejected because the remote branch has commits the push doesn't contain."""


def github_repo(url: str) -> str:
    """``owner/repo`` of a GitHub HTTPS or SSH URL; ValueError for anything else."""
    for pattern in (GITHUB_HTTPS_RE, GITHUB_SSH_RE):
        if match := pattern.fullmatch(url):
            return f"{match['owner']}/{match['repo']}"
    raise ValueError(f"not a GitHub URL: {url}")


def remote_ref(branch: str) -> str:
    """Where ``fetch`` stores the remote's ``branch`` in the local repository."""
    return f"{REMOTE_REF_PREFIX}{branch}"


def _network(repo: Path, *args: str) -> str:
    return run_git(args, repo, timeout=NETWORK_TIMEOUT_S).check().stdout


def fetch(repo: Path, url: str, branch: str) -> str:
    """Fetch ``branch`` from ``url`` into ``remote_ref(branch)``; its commit."""
    ref = remote_ref(branch)
    _network(repo, "fetch", "--quiet", "--no-tags", "--", url, f"+refs/heads/{branch}:{ref}")
    return run_git(["rev-parse", "--verify", f"{ref}^{{commit}}"], repo).check().stdout.strip()


def unpushed(repo: Path, branch: str) -> list[str]:
    """``<short sha> <subject>`` of each local ``branch`` commit the fetched remote branch
    lacks, newest first, at most ``LISTED_COMMITS`` (call ``fetch`` first)."""
    out = run_git(
        [
            "log",
            f"--max-count={LISTED_COMMITS}",
            "--format=%h %s",
            f"{remote_ref(branch)}..refs/heads/{branch}",
        ],
        repo,
    ).check()
    return out.stdout.splitlines()


def push(repo: Path, url: str, commit: str, ref: str) -> PushResult:
    """``git push <url> <commit>:<ref>``, never forced. MOVED if the remote ref moved on;
    GitError (the trimmed git error) for any other refusal or failure."""
    result = run_git(
        ["push", "--porcelain", "--", url, f"{commit}:{ref}"], repo, timeout=NETWORK_TIMEOUT_S
    )
    if result.returncode == 0:
        return PushResult.PUSHED
    if _MOVED_RE.search(result.stdout):
        return PushResult.MOVED
    # The refusal reason ("[remote rejected] (pre-receive hook declined)") is on stdout.
    refused = [line.split("\t")[-1] for line in result.stdout.splitlines() if line[:1] == "!"]
    raise command_error(replace(result, stderr="\n".join([result.stderr.strip(), *refused])))


def push_tag(repo: Path, url: str, tag: str) -> None:
    ref = f"refs/tags/{tag}"
    _network(repo, "push", "--quiet", "--", url, f"{ref}:{ref}")


def delete_branch(repo: Path, url: str, branch: str) -> None:
    """Delete ``branch`` on the remote (a push of nothing to it)."""
    _network(repo, "push", "--quiet", "--", url, f":refs/heads/{branch}")
