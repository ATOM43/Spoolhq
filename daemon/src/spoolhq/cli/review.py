"""`spool review`: run the reviewer agent on a ticket's committed work.

It builds the inputs from the ticket store and `git diff <base>...HEAD` in the folder,
and runs the real reviewer. No gates run here: items naming a configured command are
reported as not yet checked, and the reviewer judges them from the code.
"""

import threading
from pathlib import Path
from typing import Annotated

import typer

from spoolhq.cli.common import fail, settings
from spoolhq.core.config import home_dir
from spoolhq.services.agents import AgentRunner, BackendUnavailableError, available_runners
from spoolhq.services.gates import GateRun, check_done_when
from spoolhq.services.git import DirtyRepoError, GitError, ensure_clean, is_work_tree, run_git
from spoolhq.services.projects import ProjectError, load_project, project_dir
from spoolhq.services.review import ReviewInputs, ReviewResult, review
from spoolhq.services.tickets import TicketError, TicketValidationError, load_ticket

PROMPTS_DIR = "prompts"


def make_runner() -> AgentRunner:
    """The reviewer's backend; tests replace it with a fake."""
    return available_runners()[0]


def describe(result: ReviewResult) -> list[str]:
    """``✓ 1. …`` / ``✗ 2. … — reason`` per item, then the verdict and summary."""
    lines = [
        f"✓ {item.index}. {item.item}"
        if item.met
        else f"✗ {item.index}. {item.item} — {item.reason}"
        for item in result.items
    ]
    lines.append(f"verdict: {result.verdict}")
    if result.summary:
        lines.append(result.summary)
    return lines


def review_command(
    project: Annotated[str, typer.Argument(help="Project name.")],
    ticket_id: Annotated[str, typer.Argument(metavar="TICKET", help="Ticket id, like T04.")],
    path: Annotated[
        Path | None,
        typer.Option(help="Folder with the committed work (default: the project's repository)."),
    ] = None,
    base: Annotated[
        str | None,
        typer.Option(help="Ref to diff against (default: the project's default branch)."),
    ] = None,
) -> None:
    """Review a ticket's committed work; exit 0 approve, 1 changes or human, 2 not finished."""
    projects_dir = settings().projects_dir
    try:
        project_settings = load_project(project, projects_dir=projects_dir)
        ticket = load_ticket(project, ticket_id, projects_dir=projects_dir)
    except TicketValidationError as exc:
        fail("error: " + "; ".join(exc.errors))
    except (ProjectError, TicketError) as exc:
        fail(f"error: {exc}")
    folder = (path if path is not None else project_settings.repo_path).resolve()
    if not is_work_tree(folder):
        fail(f"error: not a git repository: {folder}")
    try:
        ensure_clean(folder)
        diff = run_git(["diff", f"{base or project_settings.default_branch}...HEAD"], folder)
        diff_text = diff.check().stdout
    except (DirtyRepoError, GitError) as exc:
        fail(f"error: {exc}")

    done_when = tuple(item.text for item in ticket.done_when)
    commands = project_settings.commands.model_dump()
    # Without a gate run, every item naming a configured command is unchecked.
    for index, item in enumerate(done_when, start=1):
        if any(c.status != "not_a_gate" for c in check_done_when([item], commands, GateRun(()))):
            typer.echo(f"not yet checked by the gates: {index}. {item}", err=True)
    inputs = ReviewInputs(
        ticket_id=ticket.id,
        title=ticket.meta.title,
        body=ticket.body,
        done_when=done_when,
        gate_checked={},
        diff=diff_text,
        gate_summary=(),
        worktree=folder,
    )
    try:
        result = review(
            inputs,
            make_runner(),
            home=home_dir(),
            override_dir=project_dir(project, projects_dir) / PROMPTS_DIR,
            cancel=threading.Event(),
        )
    except (ValueError, BackendUnavailableError) as exc:  # PolicyError is a ValueError
        fail(f"error: {exc}")

    if result.verdict is None:
        typer.echo(f"review did not finish: {result.run_outcome}", err=True)
        if result.summary:
            typer.echo(result.summary, err=True)
        raise typer.Exit(code=2)
    for line in describe(result):
        typer.echo(line)
    if result.verdict != "approve":
        raise typer.Exit(code=1)
