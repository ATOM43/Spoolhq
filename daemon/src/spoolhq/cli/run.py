"""`spool run`: start, follow, pause, resume, cancel, approve, reject and discard runs in
the daemon.

The daemon owns the loop, so these commands only call its API. `next` and `all` start
a run and then print one line per phase change until it ends; Ctrl-C detaches and
leaves the run going.
"""

import time
from typing import Annotated, Any

import typer

from spoolhq.cli.client import ApiClient, ApiError
from spoolhq.cli.common import fail, settings

run_app = typer.Typer(
    name="run",
    help="Run tickets with the coding agent (the daemon must be running).",
    no_args_is_help=True,
)

ProjectArg = Annotated[str, typer.Argument(help="Project name.")]
RunOption = Annotated[
    int | None, typer.Option("--run", help="Run id (default: the project's current run).")
]
POLL_S = 1.0
# Starting a run creates its worktree; give the daemon more than the default 5 s.
TIMEOUT_S = 60.0
DETACHED = "run continues in the daemon; spool run status to check"
SHORT_SHA = 7


def _client() -> ApiClient:
    return ApiClient.from_settings(settings(), timeout=TIMEOUT_S)


def _base(project: str) -> str:
    return f"/api/projects/{project}"


def _call(method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    try:
        with _client() as client:
            return client.post(path, body) if method == "POST" else client.get(path)
    except ApiError as exc:
        fail(f"error: {exc}")


def _follow(project: str) -> None:
    """Print new phase lines once per POLL_S until no worker is on the run."""
    seen = 0
    try:
        while True:
            current = _call("GET", f"{_base(project)}/runs/current")
            for phase in current["phases"]:
                if phase["id"] > seen:
                    typer.echo(phase["text"])
                    seen = phase["id"]
            if not current["working"]:
                break
            time.sleep(POLL_S)
    except KeyboardInterrupt:
        typer.echo(DETACHED)
        return
    run = current["run"]
    if run is not None and run["status"] in ("blocked", "cancelled"):
        raise typer.Exit(code=1)


def _current_run_id(project: str, run_id: int | None) -> int:
    if run_id is not None:
        return run_id
    run = _call("GET", f"{_base(project)}/runs/current")["run"]
    if run is None:
        fail(f"error: no run in '{project}'")
    return int(run["id"])


@run_app.command("next")
def next_command(
    project: ProjectArg,
    ticket: Annotated[
        str | None, typer.Argument(metavar="[TICKET]", help="A ready ticket to run instead.")
    ] = None,
) -> None:
    """Run the next ready ticket (or TICKET) and follow it."""
    _call("POST", f"{_base(project)}/runs", {"mode": "next", "ticket": ticket})
    _follow(project)


@run_app.command("all")
def all_command(project: ProjectArg) -> None:
    """Run ready tickets one after another until one doesn't finish; follow them."""
    _call("POST", f"{_base(project)}/runs", {"mode": "all", "ticket": None})
    _follow(project)


@run_app.command("pause")
def pause_command(project: ProjectArg, run_id: RunOption = None) -> None:
    """Pause the run after its current step."""
    run = _call("POST", f"{_base(project)}/runs/{_current_run_id(project, run_id)}/pause")
    typer.echo(f"run {run['id']} ({run['ticket_id']}) pauses after its current step")


@run_app.command("resume")
def resume_command(project: ProjectArg, run_id: RunOption = None) -> None:
    """Resume a paused or interrupted run now, and follow it."""
    _call("POST", f"{_base(project)}/runs/{_current_run_id(project, run_id)}/resume")
    _follow(project)


@run_app.command("cancel")
def cancel_command(project: ProjectArg, run_id: RunOption = None) -> None:
    """Cancel the run: stop the agent, remove its worktree, ticket back to ready."""
    run = _call("POST", f"{_base(project)}/runs/{_current_run_id(project, run_id)}/cancel")
    typer.echo(f"cancelling run {run['id']} ({run['ticket_id']})")


TicketArg = Annotated[str, typer.Argument(metavar="TICKET", help="Ticket id, like T04.")]


@run_app.command("approve")
@run_app.command("integrate")
def approve_command(project: ProjectArg, ticket: TicketArg) -> None:
    """Merge a ticket waiting for your approval (or for integration), and follow it."""
    _call("POST", f"{_base(project)}/tickets/{ticket}/approve")
    _follow(project)


@run_app.command("reject")
def reject_command(
    project: ProjectArg,
    ticket: TicketArg,
    note: Annotated[str, typer.Option("--note", help="What should change.")] = "",
) -> None:
    """Send a waiting ticket back to the agent with your note, and follow it."""
    if not note.strip():
        fail("error: say what should change with --note")
    _call("POST", f"{_base(project)}/tickets/{ticket}/reject", {"note": note})
    _follow(project)


def policy_line(run: dict[str, Any]) -> str:
    """The run's merge-policy hits (``needs you: …``), or ``""``."""
    policy = run.get("policy")
    return str(policy["summary"]) if policy else ""


@run_app.command("discard")
def discard_command(project: ProjectArg, ticket: TicketArg) -> None:
    """Remove an interrupted or blocked ticket's worktree and set it back to ready."""
    _call("POST", f"{_base(project)}/tickets/{ticket}/discard")
    typer.echo(f"{ticket} discarded; it is ready again")


@run_app.command("status")
def status_command(project: ProjectArg) -> None:
    """Show the project's active run, or else the last ticket merged."""
    current = _call("GET", f"{_base(project)}/runs/current")
    run = current["run"]
    if not current["active"] or run is None:
        typer.echo(f"no active run in '{project}'")
        if run is not None and run.get("pr_number") is not None:
            typer.echo(
                f"{run['ticket_id']} · {run['status']} · PR #{run['pr_number']} · {run['pr_url']}"
            )
        if run is not None and run["status"] == "awaiting_approval" and policy_line(run):
            typer.echo(f"{run['ticket_id']} · {run['status']} · {policy_line(run)}")
        merged = current.get("last_merged")
        if merged is not None:
            sha = merged["commit"][:SHORT_SHA]
            typer.echo(f"last merged: {merged['ticket_id']} · {sha} · {merged['tag']}")
        return
    tokens = current["input_tokens"] + current["output_tokens"]
    typer.echo(
        f"run {run['id']} · {run['ticket_id']} · {run['status']} · "
        f"{current['attempts']} attempts · {tokens:,} tokens"
    )
    if run.get("pr_number") is not None:
        typer.echo(f"PR #{run['pr_number']} · {run['pr_url']}")
    if policy_line(run):
        typer.echo(policy_line(run))
    if current["phases"]:
        typer.echo(current["phases"][-1]["text"])
