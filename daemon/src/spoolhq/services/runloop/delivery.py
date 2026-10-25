"""GitHub delivery: an approved run reaches the project's ``git.remote``.

Without ``git.remote`` nothing changes: ``Delivery`` is ``LocalIntegrator``. With one,
it fetches the default branch first (local main must not have commits the remote
lacks; a local main behind it is fast-forwarded), builds the squash commit on top of
the remote's main as T14 does, and pushes it before local main moves. See
``docs/github.md``.
"""

from typing import Literal

from spoolhq.services.git import (
    GitError,
    PushResult,
    RepoNotReadyError,
    advance,
    default_branch_sha,
    fetch,
    is_ancestor,
    push,
    remote_ref,
    unpushed,
)
from spoolhq.services.runloop.integration import LocalIntegrator, waiting_message
from spoolhq.services.runloop.integrator import IntegrationResult, IntegrationStatus
from spoolhq.services.runloop.model import RunContext
from spoolhq.services.runs import Attempt, Integration, IntegrationState
from spoolhq.services.tickets import Ticket

DeliveryMode = Literal["direct", "pr"]


def delivery_mode(ticket: Ticket, attempt: Attempt | None) -> DeliveryMode:
    """How an approved ticket reaches GitHub: ``review_required`` tickets go through a
    pull request, every other one is pushed directly. Every rule lives here (T18 adds
    more, which may look at the approved ``attempt``)."""
    return "pr" if ticket.meta.review_required else "direct"


def _failed(message: str) -> IntegrationResult:
    return IntegrationResult(IntegrationStatus.FAILED, message)


def ahead_message(branch: str, remote: str, commits: list[str]) -> str:
    listed = "".join(f"\n  {line}" for line in commits)
    return f"local {branch} has commits that are not on {remote}; push or reset them first:{listed}"


class Delivery(LocalIntegrator):
    """The run loop's integrator: local integration, or GitHub delivery with
    ``git.remote`` (see module doc)."""

    def _prepare(self, ctx: RunContext) -> IntegrationResult | None:
        """Fetch first: local main must contain nothing the remote lacks; behind, it is
        fast-forwarded (a dirty main checkout waits, as in T14)."""
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
            return IntegrationResult(
                IntegrationStatus.HELD, waiting_message(project, ctx.ticket_id, exc)
            )
        return None

    def _deliver(
        self, ctx: RunContext, journal: Integration, sha: str, main_sha: str
    ) -> IntegrationResult | None:
        project, remote = ctx.project, ctx.project.git.remote
        if remote is None:
            return super()._deliver(ctx, journal, sha, main_sha)
        repo, branch = project.repo_path, project.default_branch
        if not is_ancestor(repo, main_sha, remote_ref(branch)):
            # main moved locally after the fetch: never push the user's own commits.
            self._abandon(ctx, journal, restore=True)
            return _failed(ahead_message(branch, remote, unpushed(repo, branch)))
        attempt = ctx.run_log.list_attempts(ctx.run.id)[-1]
        if delivery_mode(ctx.ticket, attempt) == "pr":
            self._abandon(ctx, journal, restore=True)
            return _failed("pull requests are not supported yet")
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
