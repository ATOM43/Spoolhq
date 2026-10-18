"""The `spool` command."""

import logging
import sys
from pathlib import Path
from typing import Annotated

import typer
import uvicorn

import spoolhq
from spoolhq.api import create_app
from spoolhq.cli.agents import agents_command
from spoolhq.cli.client import ApiClient, ApiError, DaemonNotRunning
from spoolhq.cli.common import fail as _fail
from spoolhq.cli.common import settings as _settings
from spoolhq.cli.plan import plan_app
from spoolhq.cli.runs import runs_app
from spoolhq.cli.tickets import tickets_app
from spoolhq.cli.worktrees import worktrees_app
from spoolhq.core.auth import load_or_create_token, token_path
from spoolhq.core.config import Settings, ensure_home
from spoolhq.core.daemon_lock import DaemonAlreadyRunning, acquire_daemon_lock
from spoolhq.core.logs import configure_logging
from spoolhq.services.projects import (
    ProjectError,
    ProjectValidationError,
    init_project,
    load_project,
)

app = typer.Typer(
    name="spool",
    help="SpoolHQ: turn a spec into tickets and have a coding agent implement them.",
    no_args_is_help=True,
    add_completion=False,
)

project_app = typer.Typer(
    name="project",
    help="Check and manage projects.",
    no_args_is_help=True,
)
app.add_typer(project_app)
app.add_typer(tickets_app)
app.add_typer(plan_app)
app.add_typer(runs_app)
app.add_typer(worktrees_app)
app.command("agents")(agents_command)

logger = logging.getLogger("spoolhq.daemon")


@app.command()
def serve(
    port: Annotated[
        int | None,
        typer.Option(min=1, max=65535, help="Port to listen on (default: from settings, 8765)."),
    ] = None,
) -> None:
    """Start the daemon on 127.0.0.1."""
    settings = _settings(**({"port": port} if port is not None else {}))
    home = ensure_home()
    try:
        # Held until the daemon exits: startup recovery must never run while another
        # daemon has live runs.
        lock = acquire_daemon_lock(home)
    except DaemonAlreadyRunning as exc:
        _fail(f"error: {exc}")
    with lock:
        _serve(settings, home)


def _serve(settings: Settings, home: Path) -> None:
    token = load_or_create_token(home)
    log_file = configure_logging(home / "logs", settings.log_level, redact=[token])

    base_url = f"http://{settings.host}:{settings.port}"
    typer.echo(f"SpoolHQ daemon on {base_url}")
    typer.echo(f"API docs: {base_url}/docs")
    typer.echo(f"Token: {token_path(home)}  Logs: {log_file}")
    logger.info("starting daemon", extra={"host": settings.host, "port": settings.port})

    uvicorn.run(
        create_app(settings, token=token),
        host=settings.host,
        port=settings.port,
        log_config=None,
        log_level=settings.log_level.lower(),
        proxy_headers=False,
        server_header=False,
    )


@app.command()
def version() -> None:
    """Print the CLI's version and, if it is running, the daemon's."""
    typer.echo(f"spool {spoolhq.__version__}")
    settings = _settings()
    try:
        with ApiClient.from_settings(settings) as client:
            typer.echo(f"daemon {client.version()}")
    except DaemonNotRunning:
        typer.echo("daemon not running (start it with `spool serve`)")
    except ApiError as exc:
        _fail(f"error: {exc}")


@app.command()
def init(
    name: Annotated[str, typer.Argument(help="Project name: lowercase letters, digits, hyphens.")],
    repo: Annotated[Path, typer.Option(help="The existing git repository to work on.")],
    branch: Annotated[str, typer.Option(help="Branch that tickets merge into.")] = "main",
    remote: Annotated[
        str | None, typer.Option(help="GitHub URL of the repository (optional).")
    ] = None,
) -> None:
    """Create a project workspace for an existing git repository."""
    settings = _settings()
    try:
        result = init_project(
            name, repo, projects_dir=settings.projects_dir, branch=branch, remote=remote
        )
    except ProjectValidationError as exc:
        _fail("\n".join(f"error: {line}" for line in exc.errors))
    except ProjectError as exc:
        _fail(f"error: {exc}")
    typer.echo(f"Created project '{result.project.name}' at {result.path}")
    if result.missing_notes:
        missing = ", ".join(result.missing_notes)
        typer.echo(f"note: {result.project.repo_path} has no {missing} (agents read them there)")
    typer.echo(
        f"Next: write your spec in {result.path / 'CONTEXT.md'}, "
        "and check the commands in project.yaml."
    )


@project_app.command("validate")
def validate_project(
    name: Annotated[str, typer.Argument(help="Project to check.")],
) -> None:
    """Check a project's project.yaml and print every problem."""
    settings = _settings()
    try:
        load_project(name, projects_dir=settings.projects_dir)
    except ProjectError as exc:
        _fail(str(exc))
    typer.echo("valid")


def _force_utf8_streams() -> None:
    """Make stdout and stderr write UTF-8 whatever the console code page.

    Messages contain arrows (``blocked → done``), which a Windows code page such as
    cp1252 cannot encode once output is redirected to a file or pipe. Streams that are
    missing or cannot be reconfigured (replaced by a test harness) are left alone.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        encoding = str(getattr(stream, "encoding", "")).lower().replace("_", "-")
        if encoding in {"utf-8", "utf8"}:
            continue
        try:
            # `errors` is passed on, or reconfigure would reset it to "strict".
            reconfigure(encoding="utf-8", errors=getattr(stream, "errors", None))
        except (ValueError, OSError):
            continue


def main() -> None:
    """Entry point of the `spool` console script and `python -m spoolhq`."""
    _force_utf8_streams()
    app(prog_name="spool")
