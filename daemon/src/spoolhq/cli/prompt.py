"""`spool prompt show`: print the prompt the implementer agent would start with.

Read-only. It builds the inputs from the ticket store and the project settings, reads
`CLAUDE.md`, `PROGRESS.md` and `DECISIONS.md` from the project's repository at its
current checkout, and renders the initial (non-retry) prompt.
"""

from pathlib import Path
from typing import Annotated

import typer

from spoolhq.cli.common import fail, settings
from spoolhq.services.context import (
    ContextError,
    ContextInputs,
    DependencyView,
    RepoDocs,
    TicketView,
    build_implementer_prompt,
)
from spoolhq.services.projects import ProjectError, load_project, project_dir
from spoolhq.services.tickets import TicketError, list_tickets

prompt_app = typer.Typer(
    name="prompt",
    help="Show the prompt an agent starts with.",
    no_args_is_help=True,
)

CONTEXT_FILE = "CONTEXT.md"
PROMPTS_DIR = "prompts"


def _read(path: Path) -> str | None:
    """The file's text, or None if it does not exist."""
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


@prompt_app.command("show")
def show_command(
    project: Annotated[str, typer.Argument(help="Project name.")],
    ticket_id: Annotated[str, typer.Argument(metavar="TICKET", help="Ticket id, like T04.")],
) -> None:
    """Print the implementer prompt for a ticket; its size and any cuts go to stderr."""
    projects_dir = settings().projects_dir
    try:
        workspace = project_dir(project, projects_dir)
        project_settings = load_project(project, projects_dir=projects_dir)
        listing = list_tickets(project, projects_dir=projects_dir)
    except (ProjectError, TicketError) as exc:
        fail(f"error: {exc}")

    by_id = {ticket.id: ticket for ticket in listing.tickets}
    ticket = by_id.get(ticket_id)
    if ticket is None:
        broken = [entry for entry in listing.invalid if entry.file_name.startswith(f"{ticket_id}-")]
        if broken:
            fail("error: " + "; ".join(broken[0].errors))
        fail(f"error: ticket {ticket_id} not found in '{project}'")

    dependencies = tuple(
        DependencyView(dep, by_id[dep].meta.title, by_id[dep].meta.status)
        if dep in by_id
        else DependencyView(dep, "(not found)", "missing")
        for dep in ticket.meta.depends_on
    )
    repo = project_settings.repo_path
    inputs = ContextInputs(
        ticket=TicketView(
            id=ticket.id,
            title=ticket.meta.title,
            body=ticket.body,
            depends_on=dependencies,
            review_required=ticket.meta.review_required,
        ),
        spec=_read(workspace / CONTEXT_FILE),
        repo_docs=RepoDocs(
            claude_md=_read(repo / "CLAUDE.md"),
            progress_md=_read(repo / "PROGRESS.md"),
            decisions_md=_read(repo / "DECISIONS.md"),
        ),
        commands=project_settings.commands.for_implementer(),
        max_chars=project_settings.context.max_chars,
        progress_entries=project_settings.context.progress_entries,
        decisions_lines=project_settings.context.decisions_lines,
    )
    try:
        prompt = build_implementer_prompt(inputs, override_dir=workspace / PROMPTS_DIR)
    except ContextError as exc:
        fail(f"error: {exc}")

    typer.echo(prompt.text, nl=False)
    typer.echo(
        f"template: {prompt.template} · {prompt.chars:,} of {inputs.max_chars:,} characters",
        err=True,
    )
    for cut in prompt.cuts:
        typer.echo(cut, err=True)
