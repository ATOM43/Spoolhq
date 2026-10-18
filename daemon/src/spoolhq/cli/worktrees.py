"""`spool worktrees list`: a project's run worktrees and their state (read-only).

Nothing here changes anything; leftover worktrees are cleaned up when the daemon
starts. Like the other local commands, this calls the service directly.
"""

from typing import Annotated

import typer

from spoolhq.cli.common import fail, settings, table
from spoolhq.services.git import GitError, WorktreeManager
from spoolhq.services.projects import ProjectError, ProjectValidationError, load_project

worktrees_app = typer.Typer(
    name="worktrees",
    help="Show the worktrees runs work in (read-only).",
    no_args_is_help=True,
)

COLUMNS = ("TICKET", "BRANCH", "PATH", "STATE")
NONE = "-"


@worktrees_app.command("list")
def list_command(
    project: Annotated[str, typer.Argument(help="Project name.")],
) -> None:
    """List the project's worktrees: ticket, branch, path and state."""
    current = settings()
    try:
        loaded = load_project(project, projects_dir=current.projects_dir)
    except ProjectValidationError as exc:
        fail("\n".join(f"error: {line}" for line in exc.errors))
    except ProjectError as exc:
        fail(f"error: {exc}")
    try:
        manager = WorktreeManager(
            loaded.repo_path, loaded.name, loaded.default_branch, current.worktrees_dir
        )
        worktrees = manager.list_worktrees()
    except GitError as exc:
        fail(f"error: {exc}")
    if not worktrees:
        typer.echo(f"No worktrees in '{project}'.")
        return
    rows = [
        (info.ticket_id, info.branch or NONE, str(info.path), info.state.value)
        for info in worktrees
    ]
    for line in table([COLUMNS, *rows]):
        typer.echo(line)
