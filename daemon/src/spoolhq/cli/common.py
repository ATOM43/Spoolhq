"""Helpers shared by the `spool` commands."""

from typing import Any, NoReturn

import typer

from spoolhq.core.config import ConfigError, Settings, load_settings


def fail(message: str) -> NoReturn:
    """Print ``message`` to stderr and exit with status 1."""
    typer.echo(message, err=True)
    raise typer.Exit(code=1)


def settings(**overrides: Any) -> Settings:
    """Load settings, exiting with the error if they are invalid."""
    try:
        return load_settings(**overrides)
    except ConfigError as exc:
        fail(f"error: {exc}")
