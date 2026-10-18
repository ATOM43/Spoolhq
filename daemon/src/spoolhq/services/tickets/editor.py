"""Editing a ticket file in the user's editor, with a backup to restore.

The editor comes from ``$VISUAL`` or ``$EDITOR`` (``nano`` on POSIX, ``notepad`` on
Windows otherwise). The setting is split with ``shlex`` and run as an argument list,
never through a shell, so it cannot run anything but the editor named in it.
"""

import os
import shlex
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from spoolhq.services.tickets.errors import TicketError, TicketValidationError
from spoolhq.services.tickets.store import Ticket, find_ticket_file, read_ticket

EDITOR_VARIABLES = ("VISUAL", "EDITOR")


def _unquote(arg: str) -> str:
    """Windows ``shlex`` (non-POSIX) keeps quotes around an argument; drop them."""
    if len(arg) >= 2 and arg[0] == arg[-1] and arg[0] in "'\"":
        return arg[1:-1]
    return arg


def editor_command(
    environ: Mapping[str, str] | None = None, *, windows: bool | None = None
) -> list[str]:
    """The editor to run, as an argument list (the file name is added after it)."""
    env = os.environ if environ is None else environ
    is_windows = os.name == "nt" if windows is None else windows
    for variable in EDITOR_VARIABLES:
        value = env.get(variable, "").strip()
        if not value:
            continue
        try:
            # POSIX rules would treat the backslashes of Windows paths as escapes.
            args = shlex.split(value, posix=not is_windows)
        except ValueError as exc:
            raise TicketError(f"cannot read ${variable} ({value!r}): {exc}") from exc
        if is_windows:
            args = [_unquote(arg) for arg in args]
        if args and args[0]:
            return args
    return ["notepad"] if is_windows else ["nano"]


def run_editor(command: list[str], path: Path) -> int:
    """Open ``path`` in ``command`` and wait for it; returns the editor's exit status."""
    executable = shutil.which(command[0])
    if executable is None:
        raise TicketError(f"editor {command[0]!r} not found; set $VISUAL or $EDITOR")
    try:
        result = subprocess.run(  # noqa: S603 - argument list from shlex, no shell
            [executable, *command[1:], str(path)], check=False
        )
    except OSError as exc:
        raise TicketError(f"cannot start the editor {command[0]!r}: {exc}") from exc
    return result.returncode


@dataclass
class TicketEdit:
    """One editing session: the ticket file and a backup of it as it was before."""

    path: Path
    backup: Path
    command: list[str]

    def open_editor(self) -> int:
        """Run the editor on the ticket file; returns its exit status."""
        return run_editor(self.command, self.path)

    def check(self) -> Ticket:
        """Re-validate the edited file; raises TicketValidationError listing every problem."""
        try:
            return read_ticket(self.path)
        except TicketValidationError:
            raise
        except TicketError as exc:
            raise TicketValidationError([str(exc)]) from exc

    def restore(self) -> None:
        """Put the previous version back and drop the backup."""
        os.replace(self.backup, self.path)

    def finish(self) -> None:
        """Keep the edited file and drop the backup."""
        self.backup.unlink(missing_ok=True)


def start_edit(
    project: str,
    ticket_id: str,
    *,
    projects_dir: Path,
    environ: Mapping[str, str] | None = None,
) -> TicketEdit:
    """Find the ticket's file (valid or not) and back it up before editing.

    The backup is ``tickets/.<file>.bak``, a hidden file that listing ignores.
    """
    path = find_ticket_file(project, ticket_id, projects_dir=projects_dir)
    command = editor_command(environ)
    backup = path.with_name(f".{path.name}.bak")
    shutil.copy2(path, backup)
    return TicketEdit(path=path, backup=backup, command=command)
