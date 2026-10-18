"""Reading and saving the tickets of a project: ``<workspace>/tickets/<id>-<slug>.md``."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from spoolhq.core.ids import check_ticket_id
from spoolhq.services.projects import ProjectError, project_dir
from spoolhq.services.projects.errors import format_errors
from spoolhq.services.projects.yaml_io import to_plain, write_atomic
from spoolhq.services.tickets import document
from spoolhq.services.tickets.checklist import parse_done_when
from spoolhq.services.tickets.document import TicketText
from spoolhq.services.tickets.errors import (
    TICKETS_DIR,
    TicketError,
    TicketValidationError,
    source_name,
)
from spoolhq.services.tickets.model import (
    FILE_ID_CONTEXT,
    TICKET_STATUSES,
    DoneItem,
    TicketMeta,
)

FILE_NAME_RE = re.compile(r"(?P<prefix>[^-]+)-(?P<slug>.+)\.md")
FILE_NAME_RULE = "file name must be <id>-<slug>.md, like T04-project-workspace.md"


@dataclass
class Ticket:
    """One ticket file: validated frontmatter plus the body as the exact original text.

    Change ``meta`` (assignments are validated) or ``body`` and pass the ticket to
    ``save_ticket``; only the frontmatter keys that changed are rewritten.
    """

    meta: TicketMeta
    body: str
    file_name: str
    _text: TicketText = field(repr=False, compare=False)
    _loaded: dict[str, Any] = field(repr=False, compare=False)
    """The frontmatter values as loaded, to tell which keys changed."""

    @property
    def id(self) -> str:
        return self.meta.id

    @property
    def done_when(self) -> list[DoneItem]:
        """The checklist under ``## Done when``; empty if the section is missing."""
        return parse_done_when(self.body)[0]

    @property
    def warnings(self) -> list[str]:
        """Problems that do not make the ticket invalid, such as a missing Done-when."""
        return [f"{source_name(self.file_name)}: {w}" for w in parse_done_when(self.body)[1]]


@dataclass(frozen=True)
class InvalidTicket:
    """A ticket file that failed to load, with every problem found."""

    file_name: str
    errors: list[str]


@dataclass(frozen=True)
class TicketListing:
    tickets: list[Ticket]
    """Valid tickets matching the filters, sorted by id."""
    invalid: list[InvalidTicket]
    """Files that failed to load (not filtered), sorted by file name."""


def _id_sort_key(ticket_id: str) -> tuple[int, str]:
    return int(ticket_id[1:]), ticket_id


def parse_ticket(text: str, file_name: str) -> Ticket:
    """Parse the text of a ticket file; raises TicketValidationError listing every problem."""
    source = source_name(file_name)
    errors = []
    name = FILE_NAME_RE.fullmatch(file_name)
    if name is None:
        errors.append(f"{source}: {FILE_NAME_RULE}")
    try:
        parts = document.split(text, source)
    except TicketValidationError as exc:
        raise TicketValidationError(errors + exc.errors) from exc
    data = parts.doc
    meta: TicketMeta | None = None
    if data is None:
        errors.append(f"{source}: the frontmatter is empty")
    elif not isinstance(data, Mapping):
        errors.append(f"{source}: the frontmatter must be a mapping of fields")
    else:
        context = {FILE_ID_CONTEXT: name["prefix"]} if name else None
        try:
            meta = TicketMeta.model_validate(to_plain(data), context=context)
        except ValidationError as exc:
            errors.extend(format_errors(exc, TicketMeta, prefix=source))
    if errors or meta is None:
        raise TicketValidationError(errors)
    return Ticket(
        meta=meta,
        body=parts.body,
        file_name=file_name,
        _text=parts,
        _loaded=meta.model_dump(),
    )


def read_ticket(path: Path) -> Ticket:
    """Load one ticket file; raises TicketValidationError listing every problem."""
    try:
        text = path.read_bytes().decode("utf-8")
    except FileNotFoundError as exc:
        raise TicketError(f"{source_name(path.name)}: not found at {path}") from exc
    except UnicodeDecodeError as exc:
        raise TicketValidationError(
            [f"{source_name(path.name)}: not UTF-8 text (invalid byte at offset {exc.start})"]
        ) from exc
    except OSError as exc:
        raise TicketError(f"{source_name(path.name)}: cannot read {path}: {exc}") from exc
    return parse_ticket(text, path.name)


def render_ticket(ticket: Ticket) -> str:
    """The ticket file's new text: changed frontmatter keys rewritten, the body as is."""
    current = ticket.meta.model_dump()
    changes = {key: value for key, value in current.items() if ticket._loaded.get(key) != value}
    frontmatter = document.update_frontmatter(ticket._text, changes)
    return ticket._text.join(frontmatter=frontmatter, body=ticket.body)


def tickets_dir(project: str, *, projects_dir: Path) -> Path:
    """``<projects_dir>/<project>/tickets``; the project folder must exist."""
    try:
        folder = project_dir(project, projects_dir)
    except ProjectError as exc:
        raise TicketError(str(exc)) from exc
    if not folder.is_dir():
        raise TicketError(f"no project {project!r} in {projects_dir}")
    return folder / TICKETS_DIR


def _ticket_files(directory: Path) -> list[Path]:
    """The ``*.md`` files in ``tickets/``, ignoring hidden ones (``.T04-x.md.bak``).

    Sorted by file name as a string: ``Path`` ordering ignores case on Windows, which
    would order the files differently there.
    """
    if not directory.is_dir():
        return []
    return sorted(
        (
            path
            for path in directory.iterdir()
            if path.suffix == ".md" and not path.name.startswith(".") and path.is_file()
        ),
        key=lambda path: path.name,
    )


def find_ticket_file(project: str, ticket_id: str, *, projects_dir: Path) -> Path:
    """The file for ``ticket_id`` (by file-name prefix, so an invalid file is found too)."""
    try:
        check_ticket_id(ticket_id)
    except ValueError as exc:
        raise TicketError(str(exc)) from None
    directory = tickets_dir(project, projects_dir=projects_dir)
    matches = [
        path
        for path in _ticket_files(directory)
        if (name := FILE_NAME_RE.fullmatch(path.name)) and name["prefix"] == ticket_id
    ]
    if not matches:
        raise TicketError(f"no ticket {ticket_id} in project {project!r}")
    if len(matches) > 1:
        names = ", ".join(source_name(path.name) for path in matches)
        raise TicketError(f"more than one file for {ticket_id}: {names}")
    return matches[0]


def list_tickets(
    project: str,
    *,
    projects_dir: Path,
    status: str | None = None,
    phase: int | None = None,
) -> TicketListing:
    """Every ticket of ``project``, sorted by id, optionally filtered by status and phase.

    An invalid file never stops the others from loading; it is returned in ``invalid``
    with its errors.
    """
    if status is not None and status not in TICKET_STATUSES:
        expected = ", ".join(TICKET_STATUSES)
        raise TicketError(f"unknown status {status!r}; expected one of: {expected}")
    tickets: list[Ticket] = []
    invalid: list[InvalidTicket] = []
    for path in _ticket_files(tickets_dir(project, projects_dir=projects_dir)):
        try:
            ticket = read_ticket(path)
        except TicketValidationError as exc:
            invalid.append(InvalidTicket(path.name, exc.errors))
            continue
        except TicketError as exc:
            invalid.append(InvalidTicket(path.name, [str(exc)]))
            continue
        if status is not None and ticket.meta.status != status:
            continue
        if phase is not None and ticket.meta.phase != phase:
            continue
        tickets.append(ticket)
    tickets.sort(key=lambda ticket: _id_sort_key(ticket.id))
    return TicketListing(tickets=tickets, invalid=invalid)


def load_ticket(project: str, ticket_id: str, *, projects_dir: Path) -> Ticket:
    """Load the ticket ``ticket_id``; raises TicketValidationError if its file is invalid."""
    return read_ticket(find_ticket_file(project, ticket_id, projects_dir=projects_dir))


def save_ticket(project: str, ticket: Ticket, *, projects_dir: Path) -> Path:
    """Write ``ticket`` back to its file, atomically.

    Only frontmatter keys whose value changed are rewritten; comments, key order,
    quoting, line endings and the body's exact text are kept. Saving an unchanged
    ticket writes the same bytes it was read from.
    """
    path = tickets_dir(project, projects_dir=projects_dir) / ticket.file_name
    if not path.parent.is_dir():
        raise TicketError(f"no tickets folder in project {project!r}: {path.parent}")
    source = source_name(ticket.file_name)
    name = FILE_NAME_RE.fullmatch(ticket.file_name)
    context = {FILE_ID_CONTEXT: name["prefix"]} if name else None
    # model_copy(update=...) skips validation, so check the values before writing them.
    try:
        TicketMeta.model_validate(ticket.meta.model_dump(), context=context)
    except ValidationError as exc:
        raise TicketValidationError(format_errors(exc, TicketMeta, prefix=source)) from exc

    text = render_ticket(ticket)
    write_atomic(path, text)
    saved = parse_ticket(text, ticket.file_name)
    ticket._text, ticket._loaded = saved._text, saved._loaded
    return path
