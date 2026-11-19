"""`spool tickets`: list, show, add and edit a project's ticket files, and change a status.

These are local file operations, so they call the tickets service directly; the daemon
is not needed. `draft` is the exception: the daemon runs the planner and saves the drafts.
"""

import sys
import time
from pathlib import Path
from typing import Annotated, Any

import typer
from pydantic import ValidationError

from spoolhq.cli.client import ApiClient, ApiError
from spoolhq.cli.common import fail, hours, settings, table
from spoolhq.cli.runs import _run_log, _workspace
from spoolhq.services.scheduler import (
    NewTicket,
    SchedulerError,
    TicketEditError,
    apply_transition,
    create_ticket,
)
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
    help="List, show and edit a project's tickets, and change their status.",
    no_args_is_help=True,
)

ProjectArg = Annotated[str, typer.Argument(help="Project name.")]
TicketIdArg = Annotated[str, typer.Argument(help="Ticket id, like T04.")]

COLUMNS = ("ID", "STATUS", "PHASE", "TITLE", "DEPENDS ON", "ESTIMATE")
NONE = "-"
POLL_S = 1.0
DRAFT_TIMEOUT_S = 30.0


def _deps(ticket: Ticket) -> str:
    return ", ".join(ticket.meta.depends_on) or NONE


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
                hours(t.meta.estimate_h),
            )
            for t in listing.tickets
        ]
        for line in table(rows):
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


def _pull_request(project: str, ticket_id: str) -> str | None:
    """``#12 <url> (awaiting_approval)`` from the ticket's latest run, read-only."""
    with _run_log(_workspace(project)) as run_log:
        runs = run_log.list_runs(ticket_id=ticket_id, limit=1) if run_log is not None else []
    if not runs or runs[0].pr_number is None:
        return None
    return f"#{runs[0].pr_number} {runs[0].pr_url} ({runs[0].status})"


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
    if pr := _pull_request(project, ticket.id):
        fields["pull_request"] = pr
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


@tickets_app.command("new")
def new_command(
    project: ProjectArg,
    title: Annotated[str, typer.Option(help="The ticket's title.")],
    done_when: Annotated[
        list[str],
        typer.Option("--done-when", help="One checklist item the reviewer checks; repeat it."),
    ],
    depends_on: Annotated[
        str, typer.Option("--depends-on", help="Ticket ids, comma-separated: T02,T03.")
    ] = "",
    estimate: Annotated[float, typer.Option(help="Hours.")] = 1,
    phase: Annotated[
        int | None, typer.Option(min=0, help="Default: the project's highest phase.")
    ] = None,
    review_required: Annotated[bool, typer.Option("--review-required")] = False,
    scope_file: Annotated[
        Path | None,
        typer.Option("--scope-file", help="Markdown file with the scope; default: stdin."),
    ] = None,
) -> None:
    """Add a ticket; SpoolHQ assigns the next id. The scope is read from --scope-file
    or, when piped, from stdin."""
    try:
        if scope_file is not None:
            scope = scope_file.read_text(encoding="utf-8")
        else:
            scope = "" if sys.stdin.isatty() else sys.stdin.read()
        new = NewTicket(
            title=title,
            scope=scope,
            done_when="\n".join(f"- [ ] {item}" for item in done_when),
            depends_on=[dep.strip() for dep in depends_on.split(",") if dep.strip()],
            estimate_h=estimate,
            review_required=review_required,
            phase=phase,
        )
        ticket = create_ticket(project, new, projects_dir=settings().projects_dir)
    except ValidationError as exc:
        first = exc.errors()[0]
        fail(f"error: {'.'.join(str(part) for part in first['loc'])}: {first['msg']}")
    except TicketValidationError as exc:
        fail("\n".join(exc.errors))
    except TicketEditError as exc:
        fail(f"error: {exc.field}: {exc}")
    except (OSError, TicketError, SchedulerError) as exc:
        fail(f"error: {exc}")
    typer.echo(f"Added {ticket.id} ({ticket.meta.status}): tickets/{ticket.file_name}")


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
    except (typer.Abort, KeyboardInterrupt):
        edit.restore()
        typer.echo(f"Restored the previous version of tickets/{edit.path.name}.", err=True)
        raise

    edit.finish()
    for warning in ticket.warnings:
        typer.echo(f"warning: {warning}", err=True)
    typer.echo(f"Saved tickets/{edit.path.name}.")


@tickets_app.command("set-status")
def set_status_command(
    project: ProjectArg,
    ticket_id: TicketIdArg,
    status: Annotated[str, typer.Argument(help=f"New status: {', '.join(TICKET_STATUSES)}.")],
) -> None:
    """Change a ticket's status, if the transition table allows it.

    Only the status line of the file changes. See docs/scheduler.md for the table.
    """
    projects_dir = settings().projects_dir
    try:
        result = apply_transition(project, ticket_id, status, projects_dir=projects_dir)
    except TicketValidationError as exc:
        fail("\n".join(exc.errors))
    except (TicketError, SchedulerError) as exc:
        fail(f"error: {exc}")
    ticket = result.ticket
    if result.changed:
        typer.echo(f"{ticket.id}: {result.previous} → {ticket.meta.status}")
    else:
        typer.echo(f"{ticket.id} is already {ticket.meta.status}")


def _client() -> ApiClient:
    return ApiClient.from_settings(settings(), timeout=DRAFT_TIMEOUT_S)


def draft_markdown(draft: dict[str, Any]) -> str:
    """One draft as ``spool tickets draft`` prints it."""
    review = "yes" if draft["review_required"] else "no"
    deps = ", ".join(draft["depends_on"]) or "nothing"
    lines = [
        f"## {draft['ref']} · {draft['title']}",
        "",
        f"Phase {draft['phase']} · {hours(draft['estimate_h'])} · review: {review}"
        f" · depends on: {deps}",
        "",
        draft["scope"] or "(no scope)",
        "",
        "Done when:",
        *(f"- [ ] {item}" for item in draft["done_when"]),
    ]
    if draft["problems"]:
        lines += ["", "Problems:"]
        lines += [f"- {p['field']}: {p['message']}" for p in draft["problems"]]
    return "\n".join(lines) + "\n"


def _batch_item(draft: dict[str, Any]) -> dict[str, Any]:
    keep = ("ref", "title", "scope", "depends_on", "estimate_h", "review_required", "phase")
    item = {key: draft[key] for key in keep}
    item["done_when"] = "\n".join(f"- [ ] {line}" for line in draft["done_when"])
    return item


@tickets_app.command("draft")
def draft_command(
    project: ProjectArg,
    request: Annotated[
        str | None, typer.Argument(help="What the tickets should do; default: stdin.")
    ] = None,
    save: Annotated[
        bool, typer.Option("--save", help="Save the drafts, if none has a problem.")
    ] = False,
) -> None:
    """Draft one to three tickets from a few lines with the planner (the daemon must be
    running), and print them with their problems as markdown."""
    text = request if request is not None else sys.stdin.read()
    base = f"/api/projects/{project}/tickets"
    job_id: str | None = None
    try:
        with _client() as client:
            job_id = client.post(f"{base}/draft", {"request": text})["job_id"]
            job = client.get(f"{base}/draft/{job_id}")
            while job["state"] == "running":
                time.sleep(POLL_S)
                job = client.get(f"{base}/draft/{job_id}")
            if job["state"] != "succeeded":
                fail(f"error: {job['error'] or 'drafting was ' + job['state']}")
            typer.echo("\n".join(draft_markdown(draft) for draft in job["drafts"]), nl=False)
            if not save:
                return
            if any(draft["problems"] for draft in job["drafts"]):
                fail("error: not saved: fix the problems above in the app, or draft again")
            items = [_batch_item(draft) for draft in job["drafts"]]
            saved = client.post(f"{base}/batch", {"tickets": items})["tickets"]
    except ApiError as exc:
        fail(f"error: {exc}")
    except KeyboardInterrupt:
        if job_id is not None:
            with _client() as client:
                client.post(f"{base}/draft/{job_id}/cancel")
        fail("cancelled")
    for ticket in saved:
        typer.echo(
            f"Added {ticket['id']} ({ticket['meta']['status']}): tickets/{ticket['file_name']}"
        )
