"""`spool agents`: the agent backends on this machine and whether they can run.

Read-only and local: it asks each backend to detect itself and never starts an agent.
Exits 0 even when nothing is installed; the output says what to do instead. With
``--project``, it shows the backend, model and endpoint each of that project's roles uses.
"""

from typing import Annotated

import typer

from spoolhq.cli.common import fail, settings
from spoolhq.services.agents import BackendInfo, available_runners
from spoolhq.services.projects import Agents, ProjectError, Role, load_project

ROLES: tuple[Role, ...] = ("planner", "implementer", "reviewer")

NONE = "-"


def describe(info: BackendInfo) -> list[str]:
    """The lines `spool agents` prints for one backend."""
    lines = [info.name]
    if not info.installed:
        lines.append("  installed  no")
        lines.append(f"  {info.reason}")
        return lines
    lines.append(f"  installed  yes ({info.version or NONE})")
    if info.logged_in:
        lines.append(f"  login      yes ({info.auth_method or NONE}, {info.billing})")
    else:
        lines.append("  login      no (run: claude auth login)")
    if info.policy_enforceable:
        lines.append("  policy     yes (enforceable)")
    else:
        lines.append(f"  policy     no: {info.reason}")
    return lines


def describe_roles(agents: Agents) -> list[str]:
    """One line per role: its backend, model and endpoint (``default`` when not set)."""
    lines = []
    for role in ROLES:
        name = agents.backend_for(role)
        backend = agents.backends.get(name)
        model = backend.model if backend and backend.model else "default"
        endpoint = backend.base_url if backend and backend.base_url else "default"
        lines.append(f"{role:<12} {name}  model: {model}  endpoint: {endpoint}")
    return lines


def agents_command(
    project: Annotated[
        str | None, typer.Option(help="Show which backend each of this project's roles uses.")
    ] = None,
) -> None:
    """List the agent backends: installed, version, login and whether the policy holds."""
    if project is not None:
        try:
            agents = load_project(project, projects_dir=settings().projects_dir).agents
        except ProjectError as exc:
            fail(f"error: {exc}")
        for line in describe_roles(agents):
            typer.echo(line)
        return
    for index, runner in enumerate(available_runners()):
        if index:
            typer.echo("")
        for line in describe(runner.detect()):
            typer.echo(line)
