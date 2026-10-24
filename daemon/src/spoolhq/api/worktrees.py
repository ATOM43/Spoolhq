"""Startup recovery wiring: integrations, then worktrees, between the run log and git.

``recover_all_integrations`` finishes or undoes the integrations a stopped daemon left
open (``services/runloop``), before any worktree is removed.
``services/git`` knows nothing about runs, so the ``keep`` rule (a ticket whose latest
run is blocked, awaiting approval or interrupted keeps its worktree) is built here, from
each workspace's ``RunLog``.
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
from spoolhq.services.runloop import recover_integrations
from spoolhq.services.runs import RunLog, RunLogError, RunRegistry, RunStatus

logger = logging.getLogger("spoolhq.daemon")

# Interrupted runs (a crash, reboot or restart) keep their commits for T13 to resume.
KEEP_STATUSES = frozenset({RunStatus.BLOCKED, RunStatus.AWAITING_APPROVAL, RunStatus.INTERRUPTED})


def keep_for(run_log: RunLog) -> Callable[[str], bool]:
    """``keep(ticket_id)``: True when the ticket's latest run is blocked, awaiting approval
    or interrupted.

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


def recover_all_integrations(
    projects_dir: Path, worktrees_dir: Path, runs: RunRegistry
) -> dict[str, list[str]]:
    """Run ``recover_integrations`` for every workspace; a failing one is logged and skipped."""
    reports: dict[str, list[str]] = {}
    for workspace in list_workspaces(projects_dir):
        name = workspace.name
        try:
            run_log = runs.get(name).run_log
            project = load_project(name, projects_dir=projects_dir)
            reports[name] = recover_integrations(run_log, project, projects_dir, worktrees_dir)
        except (KeyError, ProjectError):
            continue  # no run log or a broken project.yaml: logged elsewhere at startup
        except Exception as exc:
            logger.error(
                "cannot recover integrations; skipping this project",
                extra={"project": name, "path": str(workspace), "error": str(exc)},
            )
            continue
        for line in reports[name]:
            logger.warning("integration recovered", extra={"project": name, "action": line})
    return reports


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
