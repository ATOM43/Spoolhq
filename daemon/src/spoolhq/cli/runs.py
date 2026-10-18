"""`spool runs`: list a project's runs and show one with its attempts.

Read-only: the commands open ``state.db`` directly in SQLite's read-only mode, so they
work without the daemon and never run recovery or change anything.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Annotated

import typer

from spoolhq.cli.common import fail, settings, table
from spoolhq.services.projects import ProjectError, project_dir
from spoolhq.services.runs import RunLog, RunLogError, Usage

runs_app = typer.Typer(
    name="runs",
    help="Show a project's runs and their attempts (read-only).",
    no_args_is_help=True,
)

ProjectArg = Annotated[str, typer.Argument(help="Project name.")]

LIST_COLUMNS = ("ID", "TICKET", "STATUS", "STARTED", "ATTEMPTS", "TOKENS")
ATTEMPT_COLUMNS = ("#", "KIND", "STATUS", "INPUT", "OUTPUT", "COST", "FOLDER")
NONE = "-"


def _workspace(project: str) -> Path:
    projects_dir = settings().projects_dir
    try:
        workspace = project_dir(project, projects_dir)
    except ProjectError as exc:
        fail(f"error: {exc}")
    if not workspace.is_dir():
        fail(f"error: no project {project!r} in {projects_dir}")
    return workspace


@contextmanager
def _run_log(workspace: Path) -> Iterator[RunLog | None]:
    """The workspace's run log opened read-only, or None if it has no ``state.db`` yet."""
    try:
        run_log = RunLog.open_read_only(workspace)
    except FileNotFoundError:
        yield None
        return
    except (RunLogError, sqlite3.Error) as exc:
        fail(f"error: {exc}")
    with run_log:
        yield run_log


def _cost(micro_usd: int | None) -> str:
    if micro_usd is None:
        return NONE
    return f"${Decimal(micro_usd).scaleb(-6):f}"


def _tokens(usage: Usage) -> str:
    return f"{usage.input_tokens} in · {usage.output_tokens} out"


@runs_app.command("list")
def list_command(
    project: ProjectArg,
    ticket: Annotated[str | None, typer.Option(help="Only this ticket's runs, like T04.")] = None,
    limit: Annotated[int, typer.Option(min=1, help="At most this many runs.")] = 50,
) -> None:
    """List runs, newest first, with their attempt count and total tokens."""
    workspace = _workspace(project)
    with _run_log(workspace) as run_log:
        rows: list[tuple[str, ...]] = []
        if run_log is not None:
            try:
                runs = run_log.list_runs(ticket_id=ticket, limit=limit)
            except ValueError as exc:
                fail(f"error: {exc}")
            for run in runs:
                attempts = run_log.list_attempts(run.id)
                usage = run_log.run_usage(run.id)
                rows.append(
                    (
                        str(run.id),
                        run.ticket_id,
                        run.status.value,
                        run.started_at,
                        str(len(attempts)),
                        str(usage.total_tokens),
                    )
                )
    if not rows:
        typer.echo(f"No runs of {ticket} yet." if ticket else f"No runs in '{project}' yet.")
        return
    for line in table([LIST_COLUMNS, *rows]):
        typer.echo(line)


@runs_app.command("show")
def show_command(
    project: ProjectArg,
    run_id: Annotated[int, typer.Argument(help="Run id, from `spool runs list`.")],
) -> None:
    """Show a run, then its attempts with their usage and folder."""
    workspace = _workspace(project)
    with _run_log(workspace) as run_log:
        if run_log is None:
            fail(f"error: run {run_id} not found")
        try:
            run = run_log.get_run(run_id)
        except KeyError as exc:
            fail(f"error: {exc.args[0]}")
        attempts = run_log.list_attempts(run_id)
        usage = run_log.run_usage(run_id)

    fields = {
        "id": str(run.id),
        "ticket": run.ticket_id,
        "status": run.status.value,
        "reason": run.reason or NONE,
        "started_at": run.started_at,
        "ended_at": run.ended_at or NONE,
        "tokens": _tokens(usage),
        "cost": _cost(usage.cost_micro_usd),
        "daemon": run.daemon_instance,
    }
    width = max(len(key) for key in fields) + 1
    for key, value in fields.items():
        typer.echo(f"{key + ':':<{width}} {value}")

    typer.echo("")
    if not attempts:
        typer.echo("Attempts: none")
        return
    typer.echo(f"Attempts ({len(attempts)}):")
    rows = [
        (
            str(attempt.number),
            attempt.kind.value,
            attempt.status.value,
            str(attempt.input_tokens),
            str(attempt.output_tokens),
            _cost(attempt.cost_micro_usd),
            attempt.dir,
        )
        for attempt in attempts
    ]
    for line in table([ATTEMPT_COLUMNS, *rows]):
        typer.echo(f"  {line}")
