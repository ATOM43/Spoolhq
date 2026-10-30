"""GitHub delivery: an approved run reaches the project's ``git.remote``.

Without ``git.remote`` nothing changes: ``Delivery`` is ``LocalIntegrator``. With one,
it fetches the default branch first (local main must not have commits the remote
lacks; a local main behind it is fast-forwarded) and builds the squash commit on top of
the remote's main as T14 does; the merge policy picks the mode (``policy.py``).
``direct``: the commit is pushed to the default branch before local main moves.
``pr``: it is pushed to ``spoolhq/<id>-<slug>`` and opened as
a pull request, and the ticket waits; a later attempt (changes requested) pushes on top
of it. Polling the pull requests is ``polling.py``. See ``docs/github.md``.
"""

import logging
from collections.abc import Callable
from datetime import datetime

from spoolhq.services.git import (
    BRANCH_PREFIX,
    GitError,
    PushResult,
    RepoNotReadyError,
    advance,
    default_branch_sha,
    delete_branch,
    fetch,
    github_repo,
    is_ancestor,
    push,
    remote_ref,
    run_git,
    unpushed,
)
from spoolhq.services.github import (
    MISSING_TOKEN,
    GitHubClient,
    GitHubError,
    create_pull,
    github_token,
)
from spoolhq.services.runloop.approval import read_artifact
from spoolhq.services.runloop.integration import Checkpoint, LocalIntegrator, waiting_message
from spoolhq.services.runloop.integrator import IntegrationResult, IntegrationStatus
from spoolhq.services.runloop.model import RunContext
from spoolhq.services.runloop.policy import DeliveryMode
from spoolhq.services.runloop.pr_body import pull_request_body, pull_request_title
from spoolhq.services.runs import (
    ArtifactName,
    EventKind,
    Integration,
    IntegrationState,
    set_pull_request,
    utc_now,
)

logger = logging.getLogger(__name__)

PR_BRANCH_PREFIX = "spoolhq/"
GitHubFactory = Callable[[str], GitHubClient]
"""Makes the API client for a token; tests pass one with a fake transport."""


def _failed(message: str) -> IntegrationResult:
    return IntegrationResult(IntegrationStatus.FAILED, message)


def _held(message: str) -> IntegrationResult:
    return IntegrationResult(IntegrationStatus.HELD, message)


def pr_branch(run_branch: str) -> str:
    """``spoolhq/<id>-<slug>`` for the run branch ``feat/<id>-<slug>`` (T08's naming)."""
    return PR_BRANCH_PREFIX + run_branch.removeprefix(BRANCH_PREFIX)


def ahead_message(branch: str, remote: str, commits: list[str]) -> str:
    listed = "".join(f"\n  {line}" for line in commits)
    return f"local {branch} has commits that are not on {remote}; push or reset them first:{listed}"


class Delivery(LocalIntegrator):
    """The run loop's integrator: local integration, or GitHub delivery with
    ``git.remote`` (see module doc)."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] = utc_now,
        checkpoint: Checkpoint | None = None,
        github: GitHubFactory = GitHubClient,
    ) -> None:
        super().__init__(clock=clock, checkpoint=checkpoint)
        self.github = github

    def integrate(self, ctx: RunContext) -> IntegrationResult:
        if ctx.project.git.remote is not None and ctx.run.pr_number is not None:
            return self._update_pr(ctx)
        return super().integrate(ctx)

    def _prepare(self, ctx: RunContext) -> IntegrationResult | None:
        """Fetch first: local main must contain nothing the remote lacks; behind, it is
        fast-forwarded (a dirty main checkout waits)."""
        project, remote = ctx.project, ctx.project.git.remote
        if remote is None:
            return None
        repo, branch = project.repo_path, project.default_branch
        try:
            remote_sha = fetch(repo, remote, branch)
        except GitError as exc:
            return _failed(f"cannot fetch {branch} from {remote}: {exc}")
        local = default_branch_sha(repo, branch)
        if local == remote_sha:
            return None
        if not is_ancestor(repo, local, remote_sha):
            return _failed(ahead_message(branch, remote, unpushed(repo, branch)))
        try:
            advance(repo, branch, remote_sha, local)
        except RepoNotReadyError as exc:
            return _held(waiting_message(project, ctx.ticket_id, exc))
        return None

    def _deliver(
        self, ctx: RunContext, journal: Integration, sha: str, main_sha: str, mode: DeliveryMode
    ) -> IntegrationResult | None:
        project, remote = ctx.project, ctx.project.git.remote
        if remote is None:
            return super()._deliver(ctx, journal, sha, main_sha, mode)
        repo, branch = project.repo_path, project.default_branch
        if not is_ancestor(repo, main_sha, remote_ref(branch)):
            # main moved locally after the fetch: never push the user's own commits.
            self._abandon(ctx, journal, restore=True)
            return _failed(ahead_message(branch, remote, unpushed(repo, branch)))
        if mode == "pr":
            return self._open_pr(ctx, journal, sha)
        return self._push_direct(ctx, journal, sha, main_sha)

    def _push_direct(
        self, ctx: RunContext, journal: Integration, sha: str, main_sha: str
    ) -> IntegrationResult | None:
        """Push to the remote's default branch, then fast-forward local main and finish.
        None when the push was refused because the remote's main moved."""
        project, tid = ctx.project, ctx.ticket_id
        repo, branch, remote = project.repo_path, project.default_branch, project.git.remote
        assert remote is not None  # noqa: S101 - checked by _deliver
        try:
            pushed = push(repo, remote, sha, f"refs/heads/{branch}")
        except GitError as exc:
            self._abandon(ctx, journal, restore=True)
            return _failed(f"cannot push to {remote}: {exc}")
        if pushed is PushResult.MOVED:
            self._abandon(ctx, journal, restore=True)
            return None
        journal = self._state(ctx, journal, IntegrationState.PUSHED)
        try:
            advanced = advance(repo, branch, sha, main_sha)
        except RepoNotReadyError:
            advanced = False
        if not advanced:
            ctx.phase(
                "integrate",
                f"{tid} · integrate · pushed; local {branch} not fast-forwarded "
                "(it moved or has changes); the next integration catches it up",
            )
        journal = self._state(ctx, journal, IntegrationState.ADVANCED)
        return self._finish(ctx, journal, sha)

    def _open_pr(self, ctx: RunContext, journal: Integration, sha: str) -> IntegrationResult:
        """Push the squash commit to the PR branch, open the pull request, store it on the
        run and remove the worktree: the ticket waits in ``awaiting_approval``."""
        project, tid = ctx.project, ctx.ticket_id
        repo, remote = project.repo_path, project.git.remote
        assert remote is not None  # noqa: S101 - checked by _deliver
        token = github_token()
        if token is None:
            self._abandon(ctx, journal, restore=True)
            return _failed(MISSING_TOKEN)
        branch = pr_branch(ctx.worktree.branch)
        try:
            pushed = push(repo, remote, sha, f"refs/heads/{branch}")
        except GitError as exc:
            self._abandon(ctx, journal, restore=True)
            return _failed(f"cannot push to {remote}: {exc}")
        if pushed is PushResult.MOVED:
            self._abandon(ctx, journal, restore=True)
            return _failed(
                f"branch {branch} on {remote} has other commits; delete it there, then "
                f"run spool run integrate {project.name} {tid}"
            )
        journal = self._state(ctx, journal, IntegrationState.PUSHED)
        approved = ctx.run_log.list_attempts(ctx.run.id)[-1]
        body = pull_request_body(
            ctx.ticket,
            ctx.run.id,
            read_artifact(ctx, approved, ArtifactName.REVIEW),
            read_artifact(ctx, approved, ArtifactName.GATES),
            (ctx.run.policy or {}).get("rules", []),
        )
        try:
            with self.github(token) as client:
                pr = create_pull(
                    client,
                    github_repo(remote),
                    head=branch,
                    base=project.default_branch,
                    title=pull_request_title(ctx.ticket),
                    body=body,
                )
        except GitHubError as exc:
            # Remove the branch again, so integrating once more starts clean.
            try:
                delete_branch(repo, remote, branch)
            except GitError as error:
                logger.warning("cannot delete the PR branch", extra={"error": str(error)})
            self._abandon(ctx, journal, restore=True)
            return _failed(f"cannot open a pull request: {exc}")
        ctx.run = set_pull_request(ctx.run_log, ctx.run.id, pr.number, pr.url, branch)
        self._state(ctx, journal, IntegrationState.PR_OPEN)
        payload = {"message": "pull request opened", "number": pr.number, "url": pr.url}
        ctx.run_log.append_event(ctx.run.id, EventKind.LOG, payload)
        ctx.worktrees.teardown(ctx.worktree)  # the branch on GitHub holds the work
        return _held(f"{tid} · PR #{pr.number} opened: {pr.url}")

    def _update_pr(self, ctx: RunContext) -> IntegrationResult:
        """After a ``pr_changes`` attempt: push the worktree's commits on top of the PR
        branch (a fast-forward, never forced) and remove the worktree again."""
        project, tid, run = ctx.project, ctx.ticket_id, ctx.run
        repo, remote, branch = project.repo_path, project.git.remote, run.pr_branch
        assert remote is not None and branch is not None  # noqa: S101 - checked by integrate
        sha = run_git(["rev-parse", "HEAD"], ctx.worktree.path).check().stdout.strip()
        try:
            pushed = push(repo, remote, sha, f"refs/heads/{branch}")
        except GitError as exc:
            return _failed(f"cannot push to {remote}: {exc}")
        if pushed is PushResult.MOVED:
            return _failed(
                f"branch {branch} on {remote} has commits this run doesn't; "
                "SpoolHQ never force-pushes, so update the pull request by hand"
            )
        ctx.worktrees.teardown(ctx.worktree)
        return _held(f"{tid} · PR #{run.pr_number} updated: {run.pr_url}")
