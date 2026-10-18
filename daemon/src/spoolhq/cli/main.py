"""The `spool` command."""

import logging
from typing import Annotated, Any, NoReturn

import typer
import uvicorn

import spoolhq
from spoolhq.api import create_app
from spoolhq.auth import load_or_create_token, token_path
from spoolhq.cli.client import ApiClient, ApiError, DaemonNotRunning
from spoolhq.config import ConfigError, Settings, ensure_home, load_settings
from spoolhq.logs import configure_logging

app = typer.Typer(
    name="spool",
    help="SpoolHQ: turn a spec into tickets and have a coding agent implement them.",
    no_args_is_help=True,
    add_completion=False,
)

logger = logging.getLogger("spoolhq.daemon")


def _fail(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(code=1)


def _settings(**overrides: Any) -> Settings:
    try:
        return load_settings(**overrides)
    except ConfigError as exc:
        _fail(f"error: {exc}")


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
