"""`spool agents`: the agent backends on this machine and whether they can run.

Read-only and local: it asks each backend to detect itself and never starts an agent.
Exits 0 even when nothing is installed; the output says what to do instead.
"""

import typer

from spoolhq.services.agents import BackendInfo, available_runners

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


def agents_command() -> None:
    """List the agent backends: installed, version, login and whether the policy holds."""
    for index, runner in enumerate(available_runners()):
        if index:
            typer.echo("")
        for line in describe(runner.detect()):
            typer.echo(line)
