"""Which status changes are allowed, and applying one to a ticket file."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from spoolhq.services.scheduler.errors import TransitionError
from spoolhq.services.scheduler.schedule import waiting_on
from spoolhq.services.tickets import (
    TICKET_STATUSES,
    Ticket,
    TicketStatus,
    list_tickets,
    load_ticket,
    save_ticket,
)
from spoolhq.services.tickets.errors import source_name

# The only source of truth for status changes; docs/scheduler.md shows the same table.
TRANSITIONS: Mapping[TicketStatus, tuple[TicketStatus, ...]] = {
    "draft": ("ready",),
    "ready": ("draft", "running"),
    # → ready: cancelled or interrupted
    "running": ("ready", "awaiting_approval", "blocked", "done"),
    # → running: changes requested; → blocked: rejected or PR closed; → done: merged
    "awaiting_approval": ("running", "blocked", "done"),
    # → running: unblocked
    "blocked": ("ready", "running"),
    "done": (),  # final
}


def parse_status(value: str) -> TicketStatus:
    """``value`` as a status; raises TransitionError if it is not one."""
    if value not in TICKET_STATUSES:
        raise TransitionError(
            f"unknown status {value!r}; expected one of: {', '.join(TICKET_STATUSES)}"
        )
    return cast(TicketStatus, value)


def check_transition(ticket: Ticket, new_status: str, plan: Sequence[Ticket]) -> None:
    """Raise TransitionError unless ``ticket`` may move to ``new_status``.

    The move must be in ``TRANSITIONS``, and moving to ``running`` also needs every
    dependency to be ``done`` (which needs a valid plan: PlanError otherwise). Setting
    the status a ticket already has is allowed and changes nothing.
    """
    status = parse_status(new_status)
    current = ticket.meta.status
    if status == current:
        return
    allowed = TRANSITIONS[current]
    if status not in allowed:
        reason = (
            f"{current} is final"
            if not allowed
            else f"from {current} a ticket can move to {' or '.join(allowed)}"
        )
        raise TransitionError(f"{ticket.id}: {current} → {status} is not allowed; {reason}")
    if status == "running":
        unmet = waiting_on(ticket, plan)
        if unmet:
            raise TransitionError(f"{ticket.id} cannot start: waits for {', '.join(unmet)}")


@dataclass(frozen=True)
class TransitionResult:
    ticket: Ticket
    previous: TicketStatus

    @property
    def changed(self) -> bool:
        return self.ticket.meta.status != self.previous


def apply_transition(
    project: str, ticket_id: str, new_status: str, *, projects_dir: Path
) -> TransitionResult:
    """Check the move of ``ticket_id`` to ``new_status`` and save it.

    Only the ``status`` line of the file changes; setting the same status writes
    nothing. Starting a ticket (``running``) is refused while any ticket file of the
    project is invalid, since its dependencies could not be checked.
    """
    status = parse_status(new_status)
    ticket = load_ticket(project, ticket_id, projects_dir=projects_dir)
    previous = ticket.meta.status
    listing = list_tickets(project, projects_dir=projects_dir)
    if status == "running" and status != previous and listing.invalid:
        names = ", ".join(source_name(invalid.file_name) for invalid in listing.invalid)
        raise TransitionError(
            f"{ticket.id} cannot start: some ticket files are invalid ({names}); "
            "run `spool plan check`"
        )
    check_transition(ticket, status, listing.tickets)
    if status != previous:
        ticket.meta.status = status
        save_ticket(project, ticket, projects_dir=projects_dir)
    return TransitionResult(ticket, previous)
