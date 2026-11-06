"""Which status changes are allowed, and applying one to a ticket file."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from spoolhq.services.scheduler.errors import TicketEditError, TicketLockedError, TransitionError
from spoolhq.services.scheduler.graph import validate_plan
from spoolhq.services.scheduler.schedule import waiting_on
from spoolhq.services.tickets import (
    TICKET_STATUSES,
    Ticket,
    TicketMeta,
    TicketStatus,
    list_tickets,
    load_ticket,
    parse_done_when,
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


LOCKED: Mapping[TicketStatus, str] = {
    "running": "running",
    "awaiting_approval": "waiting for approval",
}


def edit_ticket(
    project: str, ticket_id: str, meta: TicketMeta, body: str, *, projects_dir: Path
) -> Ticket:
    """Save a whole edited ticket (frontmatter and body) through the ticket store, so
    only changed keys are rewritten; a status change must be allowed by ``TRANSITIONS``.

    Refused while the ticket runs or waits for approval (TicketLockedError), and when
    changed dependencies are unknown or make a cycle, or a changed body has no "Done
    when" items (TicketEditError naming the field); nothing is written then. Only what
    the edit changes is checked, so an old ticket can still be fixed one part at a time."""
    ticket = load_ticket(project, ticket_id, projects_dir=projects_dir)
    if ticket.meta.status in LOCKED:
        raise TicketLockedError(f"{ticket_id} is locked while {LOCKED[ticket.meta.status]}")
    plan = [
        t for t in list_tickets(project, projects_dir=projects_dir).tickets if t.id != ticket_id
    ]
    if meta.status != ticket.meta.status:
        check_transition(ticket, meta.status, plan)
    deps_changed = meta.depends_on != ticket.meta.depends_on
    unknown = sorted(set(meta.depends_on) - {t.id for t in plan}) if deps_changed else []
    if unknown:
        raise TicketEditError(
            f"{ticket_id} depends on {', '.join(unknown)}, which does not exist",
            "meta.depends_on",
        )
    if body != ticket.body and not parse_done_when(body)[0]:
        raise TicketEditError("“Done when” needs at least one checklist item", "done_when")
    ticket.meta, ticket.body = meta, body
    for problem in validate_plan([*plan, ticket]) if deps_changed else []:
        if problem.code == "cycle" and ticket_id in problem.ticket_ids:
            raise TicketEditError(problem.message, "meta.depends_on")
    save_ticket(project, ticket, projects_dir=projects_dir)
    return ticket
