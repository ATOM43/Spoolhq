"""Tickets: the plan of work derived from a project's spec.

One markdown file per ticket in ``<workspace>/tickets/``, named ``<id>-<slug>.md``:
YAML frontmatter (``TicketMeta``) and a free-form body kept byte for byte. The format
is described in ``docs/ticket-format.md``.
"""

from spoolhq.services.tickets.checklist import parse_done_when
from spoolhq.services.tickets.editor import TicketEdit, editor_command, run_editor, start_edit
from spoolhq.services.tickets.errors import TicketError, TicketValidationError
from spoolhq.services.tickets.model import (
    MAX_ESTIMATE_H,
    TICKET_STATUSES,
    DoneItem,
    TicketMeta,
    TicketStatus,
)
from spoolhq.services.tickets.store import (
    InvalidTicket,
    Ticket,
    TicketListing,
    find_ticket_file,
    list_tickets,
    load_ticket,
    parse_ticket,
    read_ticket,
    render_ticket,
    save_ticket,
    tickets_dir,
)

__all__ = [
    "MAX_ESTIMATE_H",
    "TICKET_STATUSES",
    "DoneItem",
    "InvalidTicket",
    "Ticket",
    "TicketEdit",
    "TicketError",
    "TicketListing",
    "TicketMeta",
    "TicketStatus",
    "TicketValidationError",
    "editor_command",
    "find_ticket_file",
    "list_tickets",
    "load_ticket",
    "parse_done_when",
    "parse_ticket",
    "read_ticket",
    "render_ticket",
    "run_editor",
    "save_ticket",
    "start_edit",
    "tickets_dir",
]
