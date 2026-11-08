"""One ticket's runs, for the ticket drawer: its latest run, every attempt and its git
state (branch, commits, the squash commit and tag on main, the pull request)."""

from dataclasses import dataclass
from typing import Literal

from spoolhq.services.git import GitError, github_repo, ticket_branch
from spoolhq.services.projects import Project
from spoolhq.services.runloop.integration import tag_name
from spoolhq.services.runloop.machine import retries_used
from spoolhq.services.runs import Attempt, AttemptKind, Run, RunLog, RunStatus, ticket_merge

PrState = Literal["open", "merged", "closed"]


@dataclass(frozen=True)
class TicketGit:
    branch: str | None
    """The ticket's local branch, while it exists."""
    commits: int | None
    """Commits on that branch ahead of the default branch."""
    diff_lines: int | None
    """Lines those commits add and remove."""
    commit: str | None
    """The squash commit on the default branch, once merged."""
    commit_url: str | None
    """That commit on GitHub, with a GitHub remote."""
    tag: str | None
    pr_number: int | None
    pr_url: str | None
    pr_state: PrState | None
    pr_checked_at: str | None
    """When SpoolHQ last checked the project's open pull requests."""


@dataclass(frozen=True)
class TicketRuns:
    run: Run | None
    """The ticket's latest run."""
    attempts: list[Attempt]
    """Every attempt of the ticket, oldest first."""
    git: TicketGit
    review_retries_left: int | None = None
    """The latest run's review retries left (``limits.review_retries`` minus those used
    since its last reset); None without a run."""


def _pr_state(run: Run | None) -> PrState | None:
    if run is None or run.pr_number is None:
        return None
    if run.status is RunStatus.AWAITING_APPROVAL:
        return "open"
    return "merged" if run.status is RunStatus.DONE else "closed"


def ticket_runs(
    project: Project, run_log: RunLog, ticket_id: str, checked_at: str | None
) -> TicketRuns:
    runs = run_log.list_runs(ticket_id=ticket_id, limit=200)  # newest first
    latest = runs[0] if runs else None
    attempts = [a for run in reversed(runs) for a in run_log.list_attempts(run.id)]
    try:
        branch = ticket_branch(project.repo_path, ticket_id, project.default_branch)
    except GitError:
        branch = None  # a repo that is gone or broken: the rest still shows
    merged = ticket_merge(run_log, ticket_id)
    commit = merged.commit_sha if merged else None
    remote = project.git.remote
    url = f"https://github.com/{github_repo(remote)}/commit/{commit}" if remote and commit else None
    left = None
    if latest is not None:
        used = retries_used(run_log, latest.id, AttemptKind.REVIEW_RETRY)
        left = max(project.limits.review_retries - used, 0)
    return TicketRuns(
        run=latest,
        review_retries_left=left,
        attempts=attempts,
        git=TicketGit(
            branch=branch[0] if branch else None,
            commits=branch[1] if branch else None,
            diff_lines=branch[2] if branch else None,
            commit=commit,
            commit_url=url,
            tag=tag_name(ticket_id) if commit else None,
            pr_number=latest.pr_number if latest else None,
            pr_url=latest.pr_url if latest else None,
            pr_state=_pr_state(latest),
            pr_checked_at=checked_at if latest and latest.pr_number else None,
        ),
    )
