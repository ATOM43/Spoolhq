"""Helpers shared by the `spool` commands."""

from collections.abc import Sequence
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


def table(rows: Sequence[tuple[str, ...]]) -> list[str]:
    """Left-aligned columns two spaces apart; the first row is the header."""
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    return [
        "  ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True)).rstrip()
        for row in rows
    ]
