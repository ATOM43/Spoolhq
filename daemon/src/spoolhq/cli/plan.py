"""`spool plan`: generate a plan from the spec, show and approve it, check it, show the
next ticket and the progress figures.

These call the planner and scheduler services directly; the daemon is not needed.
`generate` runs the planner agent here, like `spool review`.
"""

import threading
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from spoolhq.cli.common import fail, hours, settings, table
from spoolhq.core.config import home_dir
from spoolhq.services.agents import AgentRunner, BackendUnavailableError
from spoolhq.services.planner import PlannerError, PlanResult, approve_plan, generate_plan
from spoolhq.services.projects import ProjectError, load_project
from spoolhq.services.scheduler import (
    PlanError,
    critical_path,
    explain_idle,
    next_ready,
    summary,
    validate_plan,
)
from spoolhq.services.tickets import InvalidTicket, TicketError, TicketListing, list_tickets

plan_app = typer.Typer(
    name="plan",
    help="Generate, review and approve a project's plan; see what runs next.",
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
    typer.echo(f"remaining:     {hours(figures.remaining_hours)}")
    path = figures.critical_path
    if path.ticket_ids:
        chain = ARROW.join(path.ticket_ids)
        typer.echo(f"critical path: {chain} ({hours(path.hours)})")
    else:
        typer.echo("critical path: none")


# generate, show, approve ------------------------------------------------------------------


def make_runner(project: str) -> AgentRunner:
    """The project's ``agents.planner`` backend; tests replace it with a fake."""
    try:
        settings_ = load_project(project, projects_dir=settings().projects_dir)
    except ProjectError as exc:
        fail(f"error: {exc}")
    return settings_.agents.runner_for("planner")


def _problem_lines(listing: TicketListing) -> list[str]:
    problems = [problem.message for problem in validate_plan(listing.tickets)]
    problems += [error for ticket in listing.invalid for error in ticket.errors]
    return [f"  {problem}" for problem in problems] or ["  none"]


def _path_line(listing: TicketListing) -> str:
    if validate_plan(listing.tickets) or listing.invalid:
        return "critical path: unknown (the plan has problems)"
    path = critical_path(listing.tickets)
    if not path.ticket_ids:
        return "critical path: none"
    return f"critical path: {ARROW.join(path.ticket_ids)} ({hours(path.hours)})"


def describe_plan(result: PlanResult, listing: TicketListing) -> list[str]:
    """Count, hours, kept and deleted tickets, the critical path and the problems."""
    written = set(result.written)
    total = sum(t.meta.estimate_h for t in listing.tickets if t.id in written)
    count = len(written)
    lines = [f"wrote {count} draft ticket{'' if count == 1 else 's'} ({hours(total)})"]
    if result.kept:
        lines.append(f"kept: {', '.join(result.kept)}")
    if result.deleted:
        lines.append(f"deleted: {', '.join(result.deleted)}")
    lines += [_path_line(listing), "problems:", *_problem_lines(listing)]
    return lines


@plan_app.command("generate")
def generate_command(
    project: ProjectArg,
    template_description: Annotated[
        Path | None,
        typer.Option(
            exists=True, dir_okay=False, help="File describing the stack template applied."
        ),
    ] = None,
) -> None:
    """Run the planner on the project's CONTEXT.md and write draft tickets."""
    projects_dir = settings().projects_dir
    description = None
    if template_description is not None:
        try:
            description = template_description.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            fail(f"error: cannot read {template_description}: {exc}")
    typer.echo("planning… (this can take a few minutes)", err=True)
    try:
        result = generate_plan(
            project,
            make_runner(project),
            projects_dir=projects_dir,
            home=home_dir(),
            template_description=description,
            cancel=threading.Event(),
        )
    except (PlannerError, BackendUnavailableError) as exc:
        fail(f"error: {exc}")
    if result.error is not None:
        fail(f"error: {result.error}")
    for line in describe_plan(result, _listing(project)):
        typer.echo(line)
    typer.echo(f"review the drafts (spool plan show {project}), then: spool plan approve {project}")


@plan_app.command("show")
def show_command(project: ProjectArg) -> None:
    """List the draft tickets with their dependencies and estimates, and the problems."""
    listing = _listing(project)
    drafts = [ticket for ticket in listing.tickets if ticket.meta.status == "draft"]
    if drafts:
        rows = [("ID", "ESTIMATE", "DEPENDS ON", "TITLE")]
        rows += [
            (
                t.id,
                hours(t.meta.estimate_h),
                ", ".join(t.meta.depends_on) or "-",
                t.meta.title,
            )
            for t in drafts
        ]
        for line in table(rows):
            typer.echo(line)
        total = sum(t.meta.estimate_h for t in drafts)
        typer.echo(f"\n{len(drafts)} drafts, {hours(total)}")
    else:
        typer.echo("no draft tickets")
    typer.echo("problems:")
    for line in _problem_lines(listing):
        typer.echo(line)


@plan_app.command("approve")
def approve_command(project: ProjectArg) -> None:
    """Check the whole plan and move every draft to ready, in one step."""
    try:
        approved = approve_plan(project, projects_dir=settings().projects_dir)
    except PlannerError as exc:
        fail(f"error: {exc}")
    typer.echo(f"approved {len(approved)} tickets: {', '.join(approved)}")
