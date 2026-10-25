"""Polling the pull requests SpoolHQ opened: merged, changes requested, or closed.

``GitHubPoller`` checks every project's open pull requests every 60 s on a daemon
thread while the daemon runs; ``sync`` does it once on demand (``spool github sync``).
A pull request is open while its ticket's latest run waits in ``awaiting_approval``
with a PR number. For each one:

- merged: fetch, fast-forward local main (a dirty main checkout waits for the next
  poll), tag the merge commit and push the tag, delete the branch, ticket ``done``.
- a ``CHANGES_REQUESTED`` review newer than the last attempt: a ``pr_changes`` attempt
  in a worktree recreated from the PR branch, with the review in its prompt; when it is
  approved, ``Delivery`` pushes it on top of the branch.
- closed without merging: ticket and run ``blocked``.

GitHub errors and rate limits never block a ticket: they are logged, and the next poll
tries again (after the time GitHub asked for). Reviews and comments are untrusted text
and are only read from SpoolHQ's own pull requests. See ``docs/github.md``.
"""

import logging
import re
import threading
from collections.abc import Callable
from datetime import datetime

from spoolhq.services.git import (
    GitError,
    RepoNotReadyError,
    advance,
    create_tag,
    default_branch_sha,
    delete_branch,
    fetch,
    github_repo,
    is_ancestor,
    run_git,
)
from spoolhq.services.github import (
    MISSING_TOKEN,
    GitHubClient,
    GitHubError,
    PullRequest,
    Review,
    get_pull,
    github_token,
    list_review_comments,
    list_reviews,
)
from spoolhq.services.projects import Project
from spoolhq.services.runloop.delivery import GitHubFactory
from spoolhq.services.runloop.integration import publish_tag, tag_name
from spoolhq.services.runloop.loop import RunLoop
from spoolhq.services.runloop.model import RunLoopError, record_phase, user_errors
from spoolhq.services.runs import (
    AttemptKind,
    EventKind,
    IntegrationState,
    Run,
    RunLog,
    RunRegistry,
    RunStatus,
    open_pull_requests,
    pull_request_integration,
    set_integration_state,
    utc_now,
)
from spoolhq.services.scheduler import apply_transition
from spoolhq.services.tickets import load_ticket

logger = logging.getLogger(__name__)

POLL_S = 60.0
FEEDBACK_MAX = 20_000
_SHA_RE = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")


def _when(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def review_text(review: Review, comments: list[tuple[str, int | None, str]]) -> str:
    """The review's body and its inline comments, as one block of untrusted text."""
    parts = [f"Review by {review.author or 'unknown'}:\n{review.body.strip() or '(no text)'}"]
    for path, line, body in comments:
        where = f"{path} line {line}" if line is not None else path
        parts.append(f"On {where}:\n{body.strip()}")
    return "\n\n".join(parts)[:FEEDBACK_MAX]


class GitHubPoller:
    """Checks the open pull requests of every project (see module doc)."""

    def __init__(
        self,
        loop: RunLoop,
        registry: RunRegistry,
        *,
        github: GitHubFactory = GitHubClient,
        clock: Callable[[], datetime] = utc_now,
        interval_s: float = POLL_S,
    ) -> None:
        self.loop = loop
        self.registry = registry
        self.github = github
        self.clock = clock
        self.interval_s = interval_s
        self.wait_until: datetime | None = None
        """Set by a rate limit: no API call before then."""
        self._sync_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._poll, name="spoolhq-github", daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(self.interval_s)

    def _poll(self) -> None:
        while not self._stop.wait(self.interval_s):
            for project in self.registry.projects:
                try:
                    for line in self.sync(project):
                        logger.info("github sync", extra={"project": project, "action": line})
                except RunLoopError as exc:  # no remote or no token: nothing to poll
                    logger.debug("github sync skipped", extra={"project": project, "why": str(exc)})
                except Exception:
                    logger.exception("github sync failed", extra={"project": project})

    def sync(self, project: str) -> list[str]:
        """Check the project's open pull requests once; one line per pull request."""
        # The run loop's own helpers: the poller acts on its runs under its lock.
        settings, _, run_log = self.loop._project(project)
        if settings.git.remote is None:
            raise RunLoopError(f"'{project}' has no git.remote")
        runs = open_pull_requests(run_log)
        if not runs:
            return []
        token = github_token()
        if token is None:
            raise RunLoopError(MISSING_TOKEN)
        if self.wait_until is not None and self.clock() < self.wait_until:
            return [f"GitHub asked to wait until {self.wait_until:%H:%M:%S} UTC; nothing checked"]
        lines = []
        with self._sync_lock, self.github(token) as client:
            for run in runs:
                try:
                    lines.append(self._check(settings, run_log, run, client))
                except GitHubError as exc:
                    logger.warning(
                        "GitHub API error; trying again at the next poll",
                        extra={"project": project, "ticket_id": run.ticket_id, "error": str(exc)},
                    )
                    lines.append(f"{run.ticket_id}: {exc}; trying again at the next poll")
                    if exc.retry_at is not None:
                        self.wait_until = exc.retry_at
                        break
                except (GitError, RunLoopError, OSError) as exc:
                    logger.warning(
                        "cannot act on the pull request; trying again at the next poll",
                        extra={"project": project, "ticket_id": run.ticket_id, "error": str(exc)},
                    )
                    lines.append(f"{run.ticket_id}: {exc}")
        return lines

    def _check(self, settings: Project, run_log: RunLog, run: Run, client: GitHubClient) -> str:
        assert settings.git.remote is not None and run.pr_number is not None  # noqa: S101
        tid, number = run.ticket_id, run.pr_number
        repo = github_repo(settings.git.remote)
        pr = get_pull(client, repo, number)
        if pr.merged:
            return self._merged(settings, run_log, run, pr)
        if pr.state == "closed":
            reason = f"PR #{number} was closed without merging"
            record_phase(run_log, run.id, "blocked", f"{tid} · blocked · {reason}")
            run_log.set_run_status(run.id, RunStatus.BLOCKED, reason)
            apply_transition(settings.name, tid, "blocked", projects_dir=self.loop.projects_dir)
            if journal := pull_request_integration(run_log, run.id):
                set_integration_state(run_log, journal.id, IntegrationState.ABANDONED)
            return f"{tid}: blocked, {reason}"
        review = self._changes_requested(client, repo, run_log, run)
        if review is None:
            return f"{tid}: PR #{number} open"
        comments = [
            (c.path, c.line, c.body)
            for c in list_review_comments(client, repo, number)
            if c.review_id == review.id
        ]
        self._revise(settings, run_log, run, review, review_text(review, comments))
        return f"{tid}: changes requested on PR #{number}; a new attempt started"

    def _changes_requested(
        self, client: GitHubClient, repo: str, run_log: RunLog, run: Run
    ) -> Review | None:
        """The newest ``CHANGES_REQUESTED`` review, if no attempt has answered it yet."""
        assert run.pr_number is not None  # noqa: S101
        reviews = [
            review
            for review in list_reviews(client, repo, run.pr_number)
            if review.state == "CHANGES_REQUESTED" and review.submitted_at
        ]
        if not reviews:
            return None
        latest = max(reviews, key=lambda review: _when(review.submitted_at or ""))
        events = run_log.events_since(0, run_id=run.id, limit=100_000)
        answered = {e.payload.get("review_id") for e in events if e.kind is EventKind.LOG}
        attempts = run_log.list_attempts(run.id)
        ended = attempts[-1].ended_at if attempts else None
        if latest.id in answered or (
            ended is not None and _when(latest.submitted_at or "") <= _when(ended)
        ):
            return None
        return latest

    def _revise(
        self, settings: Project, run_log: RunLog, run: Run, review: Review, feedback: str
    ) -> None:
        """Recreate the worktree from the PR branch and start a ``pr_changes`` attempt."""
        assert settings.git.remote is not None and run.pr_branch is not None  # noqa: S101
        loop, project, tid = self.loop, settings.name, run.ticket_id
        head = fetch(settings.repo_path, settings.git.remote, run.pr_branch)
        _, workspace, _ = loop._project(project)
        with loop._mutex:
            loop._check_free(project)
            manager = loop._manager(settings)
            with user_errors():
                if manager.resume(tid) is None:
                    ticket = load_ticket(project, tid, projects_dir=loop.projects_dir)
                    worktree = manager.create(tid, ticket.meta.title, run.id)
                    run_git(["reset", "--quiet", "--hard", head], worktree.path).check()
            payload = {
                "message": f"changes requested on PR #{run.pr_number}",
                "review_id": review.id,
                "pr_review": feedback,
            }
            run_log.append_event(run.id, EventKind.LOG, payload)
            loop._continue(settings, workspace, run_log, run, None, AttemptKind.PR_CHANGES)

    def _merged(self, settings: Project, run_log: RunLog, run: Run, pr: PullRequest) -> str:
        """Fetch, catch local main up, tag the merge commit, finish the ticket."""
        assert settings.git.remote is not None  # noqa: S101
        tid, number, tag = run.ticket_id, pr.number, tag_name(run.ticket_id)
        repo, branch, remote = settings.repo_path, settings.default_branch, settings.git.remote
        merge = pr.merge_commit_sha
        if merge is None or not _SHA_RE.fullmatch(merge):
            raise GitHubError(f"PR #{number} is merged but GitHub gave no merge commit")
        remote_sha = fetch(repo, remote, branch)
        if not is_ancestor(repo, merge, remote_sha):
            return f"{tid}: PR #{number} merged, but {merge[:7]} isn't on {branch} yet"
        local = default_branch_sha(repo, branch)
        if local != remote_sha and is_ancestor(repo, local, remote_sha):
            try:
                advance(repo, branch, remote_sha, local)
            except RepoNotReadyError:
                return (
                    f"{tid}: PR #{number} merged; main checkout has uncommitted changes in "
                    f"{repo}; waiting to fast-forward it"
                )
        create_tag(repo, tag, merge)
        publish_tag(settings, tid)
        if run.pr_branch is not None:
            try:
                delete_branch(repo, remote, run.pr_branch)
            except GitError as exc:
                logger.warning("cannot delete the PR branch", extra={"error": str(exc)})
        apply_transition(settings.name, tid, "done", projects_dir=self.loop.projects_dir)
        run_log.set_run_status(run.id, RunStatus.DONE)
        run_log.append_event(
            run.id, EventKind.INTEGRATE, {"commit": merge, "tag": tag, "pr": number}
        )
        if journal := pull_request_integration(run_log, run.id):
            set_integration_state(run_log, journal.id, IntegrationState.DONE, commit_sha=merge)
        record_phase(run_log, run.id, "done", f"{tid} · done · PR #{number} merged as {merge[:7]}")
        return f"{tid}: PR #{number} merged as {merge[:7]}; tagged {tag}"
