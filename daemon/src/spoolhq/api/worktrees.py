"""Startup worktree recovery: the daemon's wiring between the run log and git.

``services/git`` knows nothing about runs, so the ``keep`` rule (a ticket whose latest
run is blocked or awaiting approval keeps its worktree) is built here, from each
workspace's ``RunLog``.
"""

import logging
import sqlite3
from collections.abc import Callable
from pathlib import Path

from spoolhq.core.ids import TICKET_ID_RE
from spoolhq.services.git import (
    GitError,
    RecoveryReport,
    WorktreeManager,
    check_git_version,
    recover_worktrees,
)
from spoolhq.services.projects import ProjectError, list_workspaces, load_project
from spoolhq.services.runs import RunLog, RunLogError, RunRegistry, RunStatus

logger = logging.getLogger("spoolhq.daemon")

KEEP_STATUSES = frozenset({RunStatus.BLOCKED, RunStatus.AWAITING_APPROVAL})


def keep_for(run_log: RunLog) -> Callable[[str], bool]:
    """``keep(ticket_id)``: True when the ticket's latest run is blocked or awaiting approval.

    If the run log can't be read, the worktree is kept: removing work that a person
    may still need is worse than leaving a folder behind.
    """

    def keep(ticket_id: str) -> bool:
        if not TICKET_ID_RE.fullmatch(ticket_id):
            return False
        try:
            runs = run_log.list_runs(ticket_id=ticket_id, limit=1)
        except (sqlite3.Error, RunLogError, ValueError) as exc:
            logger.error(
                "cannot read the run log; keeping the worktree",
                extra={"ticket_id": ticket_id, "error": str(exc)},
            )
            return True
        return bool(runs) and runs[0].status in KEEP_STATUSES

    return keep


def check_git() -> None:
    """Log an error if git is missing or older than 2.36; the daemon keeps serving."""
    try:
        version = check_git_version()
    except GitError as exc:
        logger.error("git check failed", extra={"error": str(exc)})
        return
    logger.info("git found", extra={"git_version": ".".join(str(part) for part in version)})


def recover_all_worktrees(
    projects_dir: Path, worktrees_dir: Path, runs: RunRegistry
) -> dict[str, RecoveryReport]:
    """Run ``recover_worktrees`` for every workspace; a failing one is logged and skipped."""
    reports: dict[str, RecoveryReport] = {}
    for workspace in list_workspaces(projects_dir):
        project_name = workspace.name
        try:
            run_log = runs.get(project_name).run_log
        except KeyError:
            # The run registry already logged why the run log could not be opened.
            logger.warning(
                "no run log; skipping worktree recovery for this project",
                extra={"project": project_name, "path": str(workspace)},
            )
            continue
        try:
            project = load_project(project_name, projects_dir=projects_dir)
            manager = WorktreeManager(
                project.repo_path, project.name, project.default_branch, worktrees_dir
            )
            reports[project_name] = recover_worktrees(manager, keep_for(run_log))
        except (ProjectError, GitError, OSError) as exc:
            logger.error(
                "cannot recover worktrees; skipping this project",
                extra={"project": project_name, "path": str(workspace), "error": str(exc)},
            )
    return reports
