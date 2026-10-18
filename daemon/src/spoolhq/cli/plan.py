"""`spool plan`: check a project's plan, show the next ticket and the progress figures.

These are local file operations, so they call the scheduler service directly; the daemon
is not needed.
"""

from typing import Annotated, NoReturn

import typer

from spoolhq.cli.common import fail, settings
from spoolhq.services.scheduler import (
    PlanError,
    explain_idle,
    next_ready,
    summary,
    validate_plan,
)
from spoolhq.services.tickets import InvalidTicket, TicketError, TicketListing, list_tickets

plan_app = typer.Typer(
    name="plan",
    help="Check a project's plan and see what runs next.",
    no_args_is_help=True,
)

ProjectArg = Annotated[str, typer.Argument(help="Project name.")]

ARROW = " → "


def _listing(project: str) -> TicketListing:
    try:
        return list_tickets(project, projects_dir=settings().projects_dir)
    except TicketError as exc:
        fail(f"error: {exc}")


def _invalid_lines(invalid: list[InvalidTicket]) -> list[str]:
    lines = [f"Invalid ticket files ({len(invalid)}):"]
    lines += [f"  {error}" for ticket in invalid for error in ticket.errors]
    return lines


def _valid_listing(project: str) -> TicketListing:
    """The project's tickets; exits with the errors if a file or the plan is invalid."""
    listing = _listing(project)
    if listing.invalid:
        fail("\n".join([*_invalid_lines(listing.invalid), "Fix them first (spool plan check)."]))
    return listing


def _plan_failed(exc: PlanError) -> NoReturn:
    fail(f"error: {exc}")


def _hours(value: float) -> str:
    return f"{value:g}h"


@plan_app.command("check")
def check_command(project: ProjectArg) -> None:
    """Check the whole plan: dependencies, cycles, duplicate ids and invalid files."""
    listing = _listing(project)
    problems = validate_plan(listing.tickets)
    lines: list[str] = []
    if problems:
        lines.append(f"Plan problems ({len(problems)}):")
        lines += [f"  {problem.message}" for problem in problems]
    if listing.invalid:
        if lines:
            lines.append("")
        lines += _invalid_lines(listing.invalid)
    if lines:
        for line in lines:
            typer.echo(line)
        raise typer.Exit(code=1)
    count = len(listing.tickets)
    typer.echo(f"plan is valid ({count} ticket{'' if count == 1 else 's'})")


@plan_app.command("next")
def next_command(project: ProjectArg) -> None:
    """Show the ticket that runs next, or why none can."""
    tickets = _valid_listing(project).tickets
    try:
        ticket = next_ready(tickets)
        reason = explain_idle(tickets)
    except PlanError as exc:
        _plan_failed(exc)
    if ticket is not None:
        typer.echo(f"{ticket.id} · {ticket.meta.title}")
    elif reason is not None:
        typer.echo(f"nothing to run: {reason.message}")


@plan_app.command("summary")
def summary_command(project: ProjectArg) -> None:
    """Tickets per status, the hours left and the critical path."""
    tickets = _valid_listing(project).tickets
    try:
        figures = summary(tickets)
    except PlanError as exc:
        _plan_failed(exc)
    width = max(len(status) for status in figures.counts) + 1
    for status, count in figures.counts.items():
        typer.echo(f"{status + ':':<{width}} {count}")
    typer.echo("")
    typer.echo(f"remaining:     {_hours(figures.remaining_hours)}")
    path = figures.critical_path
    if path.ticket_ids:
        chain = ARROW.join(path.ticket_ids)
        typer.echo(f"critical path: {chain} ({_hours(path.hours)})")
    else:
        typer.echo("critical path: none")
