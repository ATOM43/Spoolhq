"""`spool tickets`: list, show and edit a project's ticket files.

These are local file operations, so they call the tickets service directly; the daemon
is not needed.
"""

from collections.abc import Sequence
from typing import Annotated

import typer

from spoolhq.cli.common import fail, settings
from spoolhq.services.tickets import (
    TICKET_STATUSES,
    Ticket,
    TicketError,
    TicketValidationError,
    list_tickets,
    load_ticket,
    start_edit,
)

tickets_app = typer.Typer(
    name="tickets",
    help="List, show and edit a project's tickets.",
    no_args_is_help=True,
)

ProjectArg = Annotated[str, typer.Argument(help="Project name.")]
TicketIdArg = Annotated[str, typer.Argument(help="Ticket id, like T04.")]

COLUMNS = ("ID", "STATUS", "PHASE", "TITLE", "DEPENDS ON", "ESTIMATE")
NONE = "-"


def _hours(value: float) -> str:
    return f"{value:g}h"


def _deps(ticket: Ticket) -> str:
    return ", ".join(ticket.meta.depends_on) or NONE


def _table(rows: Sequence[tuple[str, ...]]) -> list[str]:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    return [
        "  ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True)).rstrip()
        for row in rows
    ]


@tickets_app.command("list")
def list_command(
    project: ProjectArg,
    status: Annotated[
        str | None, typer.Option(help=f"Only this status: {', '.join(TICKET_STATUSES)}.")
    ] = None,
    phase: Annotated[int | None, typer.Option(min=0, help="Only this phase.")] = None,
) -> None:
    """List tickets sorted by id; invalid files are listed at the end with their errors."""
    projects_dir = settings().projects_dir
    try:
        listing = list_tickets(project, projects_dir=projects_dir, status=status, phase=phase)
    except TicketError as exc:
        fail(f"error: {exc}")

    if listing.tickets:
        rows = [COLUMNS] + [
            (
                t.id,
                t.meta.status,
                str(t.meta.phase),
                t.meta.title,
                _deps(t),
                _hours(t.meta.estimate_h),
            )
            for t in listing.tickets
        ]
        for line in _table(rows):
            typer.echo(line)
    elif not listing.invalid:
        filtered = status is not None or phase is not None
        typer.echo("No tickets match." if filtered else f"No tickets in '{project}' yet.")

    if listing.invalid:
        if listing.tickets:
            typer.echo("")
        typer.echo(f"Invalid tickets ({len(listing.invalid)}):")
        for invalid in listing.invalid:
            for error in invalid.errors:
                typer.echo(f"  {error}")
        raise typer.Exit(code=1)


@tickets_app.command("show")
def show_command(project: ProjectArg, ticket_id: TicketIdArg) -> None:
    """Show a ticket's fields, its Done-when checklist and its body."""
    projects_dir = settings().projects_dir
    try:
        ticket = load_ticket(project, ticket_id, projects_dir=projects_dir)
    except TicketValidationError as exc:
        fail("\n".join(exc.errors))
    except TicketError as exc:
        fail(f"error: {exc}")

    meta = ticket.meta
    fields = {
        "id": meta.id,
        "title": meta.title,
        "phase": str(meta.phase),
        "depends_on": _deps(ticket),
        "status": meta.status,
        "estimate_h": f"{meta.estimate_h:g}",
        "review_required": "true" if meta.review_required else "false",
        "tracker_ref": meta.tracker_ref if meta.tracker_ref is not None else "null",
    }
    width = max(len(key) for key in fields) + 1
    for key, value in fields.items():
        typer.echo(f"{key + ':':<{width}} {value}")

    typer.echo("")
    typer.echo("Done when:")
    for item in ticket.done_when:
        typer.echo(f"  [{'x' if item.checked else ' '}] {item.text}")
    if not ticket.done_when:
        typer.echo("  (none)")

    typer.echo("")
    typer.echo(f"--- {ticket.file_name} ---")
    typer.echo(ticket.body.replace("\r\n", "\n").strip("\n"))
    for warning in ticket.warnings:
        typer.echo(f"warning: {warning}", err=True)


@tickets_app.command("edit")
def edit_command(project: ProjectArg, ticket_id: TicketIdArg) -> None:
    """Open a ticket in $VISUAL / $EDITOR, then check it.

    If the edited file is invalid, you can reopen the editor or restore the previous
    version.
    """
    projects_dir = settings().projects_dir
    try:
        edit = start_edit(project, ticket_id, projects_dir=projects_dir)
    except TicketError as exc:
        fail(f"error: {exc}")

    try:
        while True:
            status = edit.open_editor()
            if status != 0:
                typer.echo(f"warning: the editor exited with status {status}", err=True)
            try:
                ticket = edit.check()
            except TicketValidationError as exc:
                typer.echo("\n".join(exc.errors), err=True)
                if typer.confirm("The ticket is invalid. Reopen the editor?", default=True):
                    continue
                edit.restore()
                fail(f"Restored the previous version of tickets/{edit.path.name}.")
            break
    except TicketError as exc:
        edit.restore()
        fail(f"error: {exc}")
    except typer.Abort:
        edit.restore()
        typer.echo(f"Restored the previous version of tickets/{edit.path.name}.", err=True)
        raise

    edit.finish()
    for warning in ticket.warnings:
        typer.echo(f"warning: {warning}", err=True)
    typer.echo(f"Saved tickets/{edit.path.name}.")
