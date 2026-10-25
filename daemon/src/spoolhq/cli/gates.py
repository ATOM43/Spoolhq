"""`spool gates run`: run a project's install, lint and test gates in a folder.

It calls the service directly, like the other local commands. The logs go to a new
temporary folder, whose path is printed.
"""

import tempfile
from pathlib import Path
from typing import Annotated

import typer

from spoolhq.cli.common import fail, settings
from spoolhq.services.gates import GateResult, GateRun, GateStatus, run_gates
from spoolhq.services.projects import ProjectError, load_project

gates_app = typer.Typer(
    name="gates",
    help="Run a project's quality gates.",
    no_args_is_help=True,
)


def describe(result: GateResult) -> str:
    """``✓ lint  just lint  4.2 s`` or ``✗ test  just test  exit 1  12.8 s``."""
    if result.status is GateStatus.SKIPPED:
        return f"- {result.name}  {result.command}  skipped"
    if result.status is GateStatus.PASSED:
        return f"✓ {result.name}  {result.command}  {result.duration_s:.1f} s"
    detail = {
        GateStatus.FAILED: f"exit {result.exit_code}",
        GateStatus.TIMED_OUT: "timed out",
        GateStatus.ERROR: "error",
    }[result.status]
    return f"✗ {result.name}  {result.command}  {detail}  {result.duration_s:.1f} s"


@gates_app.command("run")
def run_command(
    project: Annotated[str, typer.Argument(help="Project name.")],
    path: Annotated[
        Path | None,
        typer.Option(help="Folder to run the gates in (default: the project's repository)."),
    ] = None,
) -> None:
    """Run install, lint and test; exit 1 unless all pass."""
    try:
        project_settings = load_project(project, projects_dir=settings().projects_dir)
    except ProjectError as exc:
        fail(f"error: {exc}")
    folder = path if path is not None else project_settings.repo_path
    if not folder.is_dir():
        fail(f"error: not a folder: {folder}")

    log_dir = Path(tempfile.mkdtemp(prefix="spoolhq-gates-"))
    typer.echo(f"logs: {log_dir}")
    run = run_gates(
        folder,
        project_settings.commands.model_dump(),
        project_settings.gates.timeouts.model_dump(),
        log_dir,
    )
    print_run(run)
    if not run.passed:
        raise typer.Exit(code=1)


def print_run(run: GateRun) -> None:
    """One line per gate, then each failure's excerpt and failing tests."""
    for result in run.results:
        typer.echo(describe(result))
    for result in run.results:
        if result.status in (GateStatus.PASSED, GateStatus.SKIPPED):
            continue
        typer.echo(f"\n── {result.name} ──\n{result.excerpt}")
        if result.failing_tests:
            typer.echo("failing tests:")
            for name in result.failing_tests:
                typer.echo(f"  {name}")
