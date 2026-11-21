"""`spool tracker status|push [--dry-run]`: a project's tracker sync.

`status` and `push` ask the daemon, whose thread sends the queued actions. `push
--dry-run` needs no daemon: it reads the files and the run log and prints what a push
would do, changing nothing locally or in the tracker.
"""

from typing import Annotated

import typer

from spoolhq.cli.client import ApiClient, ApiError
from spoolhq.cli.common import fail, settings
from spoolhq.services.projects import ProjectError
from spoolhq.services.tickets import TicketError
from spoolhq.services.tracker.dryrun import push_plan

tracker_app = typer.Typer(name="tracker", help="Tracker sync (ClickUp).", no_args_is_help=True)

ProjectArg = Annotated[str, typer.Argument(help="Project name.")]


def _client() -> ApiClient:
    return ApiClient.from_settings(settings())


@tracker_app.command("status")
def status_command(project: ProjectArg) -> None:
    """Show the sync state: off, ok, syncing or failed, with what is waiting."""
    try:
        with _client() as client:
            view = client.get(f"/api/projects/{project}/tracker")
    except ApiError as exc:
        fail(f"error: {exc}")
    if view["state"] == "off":
        typer.echo(f"{project}: no tracker (add a tracker block to project.yaml)")
        return
    typer.echo(f"{project}: {view['kind']} · {view['state']} · {view['pending']} pending")
    typer.echo(f"last synced: {view['last_synced_at'] or 'never'}")
    if view["last_error"]:
        typer.echo(f"last error: {view['last_error']}")


@tracker_app.command("push")
def push_command(
    project: ProjectArg,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Print what would be sent; change nothing.")
    ] = False,
) -> None:
    """Queue a push of every ticket; the daemon sends it in the background."""
    if dry_run:
        try:
            lines = push_plan(project, projects_dir=settings().projects_dir)
        except (ProjectError, TicketError) as exc:
            fail(f"error: {exc}")
        for line in lines:
            typer.echo(line)
        typer.echo(f"dry run: {len(lines)} action(s), nothing sent")
        return
    try:
        with _client() as client:
            queued = client.post(f"/api/projects/{project}/tracker/push")["queued"]
    except ApiError as exc:
        fail(f"error: {exc}")
    typer.echo(f"queued {queued} action(s); see `spool tracker status {project}`")
