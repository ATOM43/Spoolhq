"""The `spool` command."""

import logging
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from types import FrameType
from typing import Annotated

import typer
import uvicorn
from pydantic import ValidationError

import spoolhq
from spoolhq.api import create_app
from spoolhq.cli.agents import agents_command
from spoolhq.cli.client import ApiClient, ApiError, DaemonNotRunning
from spoolhq.cli.common import fail as _fail
from spoolhq.cli.common import settings as _settings
from spoolhq.cli.gates import gates_app
from spoolhq.cli.github import github_app, secrets_app
from spoolhq.cli.plan import plan_app
from spoolhq.cli.prompt import prompt_app
from spoolhq.cli.review import review_command
from spoolhq.cli.run import run_app
from spoolhq.cli.runs import runs_app
from spoolhq.cli.templates import templates_app
from spoolhq.cli.tickets import tickets_app
from spoolhq.cli.worktrees import worktrees_app
from spoolhq.core.auth import load_or_create_token, token_path
from spoolhq.core.config import Settings, ensure_home, home_dir
from spoolhq.core.daemon_lock import DaemonAlreadyRunning, acquire_daemon_lock
from spoolhq.core.logs import configure_logging
from spoolhq.services.creation import (
    CreateProject,
    CreationError,
    Job,
    Local,
    Runner,
    StackCommands,
    check_request,
)
from spoolhq.services.creation.request import MergePreset, Source
from spoolhq.services.github import github_token
from spoolhq.services.projects import ProjectError, load_project
from spoolhq.services.projects.workspace import REPO_NOTES
from spoolhq.services.templates import TemplateError, load_contract, open_template

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
app.add_typer(prompt_app)
app.add_typer(gates_app)
app.add_typer(runs_app)
app.add_typer(run_app)
app.add_typer(worktrees_app)
app.add_typer(templates_app)
app.add_typer(github_app)
app.add_typer(secrets_app)
app.command("agents")(agents_command)
app.command("review")(review_command)

logger = logging.getLogger("spoolhq.daemon")


@app.command()
def serve() -> None:
    """Start the daemon on 127.0.0.1 (the port comes from SPOOLHQ_PORT or config.toml)."""
    settings = _settings()
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
    secrets = [token, *filter(None, [github_token()])]
    log_file = configure_logging(home / "logs", settings.log_level, redact=secrets)

    base_url = f"http://{settings.host}:{settings.port}"
    typer.echo(f"SpoolHQ daemon on {base_url}")
    typer.echo(f"API docs: {base_url}/docs")
    typer.echo(f"Token: {token_path(home)}  Logs: {log_file}")
    logger.info("starting daemon", extra={"host": settings.host, "port": settings.port})

    app = create_app(settings, token=token)
    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_config=None,
        log_level=settings.log_level.lower(),
        proxy_headers=False,
        server_header=False,
    )
    _Server(config, app.state.streams.close_all).run()


class _Server(uvicorn.Server):
    """Closes the event streams with 1001 when asked to stop, before uvicorn's own
    shutdown would close them as a restart (1012)."""

    def __init__(self, config: uvicorn.Config, close_streams: Callable[[], None]) -> None:
        super().__init__(config)
        self._close_streams = close_streams

    def handle_exit(self, sig: int, frame: FrameType | None) -> None:
        self._close_streams()
        super().handle_exit(sig, frame)


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


CommandOption = Annotated[
    str | None, typer.Option(help="Stack command; required unless --source empty.")
]


@app.command()
def init(
    name: Annotated[str, typer.Argument(help="Project name: lowercase letters, digits, hyphens.")],
    repo: Annotated[
        Path,
        typer.Option(
            help="The existing git repository; for a template or empty repo, a new or empty folder."
        ),
    ],
    source: Annotated[
        Source | None,
        typer.Option(help="template, existing or empty (default: template with --template)."),
    ] = None,
    template: Annotated[
        str | None,
        typer.Option(help="A built-in template (spool templates list), a folder or a git URL."),
    ] = None,
    template_ref: Annotated[
        str | None, typer.Option(help="Branch, tag or commit of a git template.")
    ] = None,
    branch: Annotated[
        str | None,
        typer.Option(help="First branch of a template or empty repo (default: main)."),
    ] = None,
    install: CommandOption = None,
    lint: CommandOption = None,
    test: CommandOption = None,
    remote: Annotated[
        str | None, typer.Option(help="GitHub URL of the repository (optional).")
    ] = None,
    merge_preset: Annotated[
        MergePreset, typer.Option(help="When a ticket needs you before it merges.")
    ] = "direct_unless_risky",
    clickup_list: Annotated[
        str | None, typer.Option(help="ClickUp list id to sync tickets with (optional).")
    ] = None,
) -> None:
    """Create a project: generate its repo from a template, use an existing git
    repository or start an empty one, check the stack commands and make the first
    commit. A failed step undoes what was created. Same service as POST /api/projects,
    which takes built-in templates only; a folder or URL template passes the same
    Copier safety check."""
    settings = _settings()
    commands = {"install": install, "lint": lint, "test": test}
    if template is not None and None in commands.values():
        # The template's own commands, unless given: what the app's dialog pre-fills.
        try:
            with open_template(template, template_ref) as found:
                defaults = load_contract(found.root, found.label).commands.gates()
        except TemplateError as exc:
            _fail(f"error: template: {exc}")
        commands = {gate: value or defaults[gate] for gate, value in commands.items()}
    try:
        request = CreateProject(
            name=name,
            source=source or ("template" if template is not None else "existing"),
            repo_path=str(repo.expanduser().absolute()),
            template=template,
            commands=StackCommands(**commands),
            git_remote=remote,
            merge_preset=merge_preset,
            clickup_list_id=clickup_list,
        )
        checked = check_request(
            request,
            projects_dir=settings.projects_dir,
            worktrees_dir=settings.worktrees_dir,
            home=home_dir(),
            local=Local(template_ref=template_ref, branch=branch),
        )
    except ValidationError as exc:
        _fail("\n".join(f"error: {error['msg']}" for error in exc.errors()))
    except CreationError as exc:
        _fail(f"error: {exc.field}: {exc.message}")
    job = Job(id="cli", project=name, source=request.source)
    lock, cancel = threading.Lock(), threading.Event()
    Runner(job, checked, projects_dir=settings.projects_dir, cancel=cancel, lock=lock).run()
    for step in job.steps:
        typer.echo(f"{step.state:<8} {step.title}")
    if job.state != "succeeded":
        failed = next(step for step in job.steps if step.state == "failed")
        lines = [f"error: {failed.field or failed.name}: {failed.message}"]
        lines += (failed.output or "").splitlines()
        if job.rollback is not None:
            lines += [f"removed {path}" for path in job.rollback.removed]
            lines += [f"error: couldn't remove {path}" for path in job.rollback.left]
        _fail("\n".join(lines))
    workspace = settings.projects_dir / name
    typer.echo(f"Created project '{name}' at {workspace}")
    missing = [note for note in REPO_NOTES if not (checked.repo / note).exists()]
    if missing:
        typer.echo(f"note: {checked.repo} has no {', '.join(missing)} (agents read them there)")
    typer.echo(f"Next: write your spec in {workspace / 'CONTEXT.md'}.")


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
