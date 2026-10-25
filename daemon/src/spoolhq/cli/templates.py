"""`spool templates list|check`: the built-in templates and the contract check.

Both call the service directly, like the other local commands.
"""

import tempfile
import time
from pathlib import Path
from typing import Annotated

import typer

from spoolhq.cli.common import fail
from spoolhq.cli.gates import print_run
from spoolhq.services.templates import (
    ResolvedTemplate,
    TemplateError,
    builtin_descriptions,
    check_template,
)

templates_app = typer.Typer(
    name="templates",
    help="List the built-in project templates and check a template's contract.",
    no_args_is_help=True,
)

RefOption = Annotated[str | None, typer.Option(help="Branch, tag or commit of a git URL template.")]


def describe_source(template: ResolvedTemplate) -> str:
    """``template: fastapi-react (built-in, spoolhq 0.0.0)`` or the URL and commit."""
    if template.kind == "builtin":
        return f"template: {template.source} (built-in, spoolhq {template.ref})"
    if template.ref is None:
        return f"template: {template.source}"
    return f"template: {template.source} at commit {template.ref}"


@templates_app.command("list")
def list_command() -> None:
    """Show the built-in templates with their descriptions."""
    try:
        templates = builtin_descriptions()
    except TemplateError as exc:
        fail(f"error: {exc}")
    for name, description in templates:
        typer.echo(name)
        for line in description.strip().splitlines():
            typer.echo(f"  {line}")


@templates_app.command("check")
def check_command(
    source: Annotated[str, typer.Argument(help="Built-in name, local folder or git URL.")],
    ref: RefOption = None,
) -> None:
    """Generate the template into a temp folder and run its install, lint and test."""
    log_dir = Path(tempfile.mkdtemp(prefix="spoolhq-template-check-logs-"))
    typer.echo(f"logs: {log_dir}")
    started = time.monotonic()
    try:
        result = check_template(
            source,
            ref=ref,
            log_dir=log_dir,
            on_resolved=lambda template: typer.echo(describe_source(template)),
        )
    except TemplateError as exc:
        fail("\n".join(f"error: {line}" for line in str(exc).splitlines()))
    print_run(result.run)
    verdict = "passes" if result.run.passed else "fails"
    elapsed = time.monotonic() - started
    typer.echo(f"template '{result.contract.name}' {verdict} its contract ({elapsed:.0f} s)")
    if not result.run.passed:
        raise typer.Exit(code=1)
