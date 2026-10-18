"""Which ticket runs next, and why nothing can when none is ready."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

from spoolhq.services.scheduler.graph import require_valid, sort_ids, sort_tickets
from spoolhq.services.tickets import Ticket, TicketStatus

IdleCode = Literal[
    "all_done", "running", "awaiting_approval", "blocked", "waiting", "plan_not_approved"
]


@dataclass(frozen=True)
class IdleReason:
    """Why ``next_ready`` found nothing to run."""

    code: IdleCode
    ticket_ids: tuple[str, ...]
    """The tickets the reason is about, sorted by id (empty for ``all_done``)."""
    message: str
    waits_for: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    """For ``waiting``: each ready ticket and the dependencies that are not done."""


def _unmet(ticket: Ticket, statuses: Mapping[str, TicketStatus]) -> list[str]:
    return sort_ids(dep for dep in ticket.meta.depends_on if statuses.get(dep) != "done")


def _statuses(tickets: Sequence[Ticket]) -> dict[str, TicketStatus]:
    return {ticket.id: ticket.meta.status for ticket in tickets}


def waiting_on(ticket: Ticket, tickets: Sequence[Ticket]) -> list[str]:
    """The ids of ``ticket``'s dependencies that are not ``done``, sorted by id.

    ``tickets`` is the plan; ``ticket`` is added to it for the check if its id is not
    in it. Raises PlanError if the plan is invalid.
    """
    plan = list(tickets)
    if ticket.id not in {t.id for t in plan}:
        plan.append(ticket)
    require_valid(plan)
    return _unmet(ticket, _statuses(plan))


def next_ready(tickets: Sequence[Ticket]) -> Ticket | None:
    """The lowest-numbered ``ready`` ticket whose dependencies are all ``done``, or None.

    Raises PlanError if the plan is invalid.
    """
    require_valid(tickets)
    statuses = _statuses(tickets)
    for ticket in sort_tickets(tickets):
        if ticket.meta.status == "ready" and not _unmet(ticket, statuses):
            return ticket
    return None


def _ids(tickets: Sequence[Ticket], status: TicketStatus) -> tuple[str, ...]:
    return tuple(t.id for t in sort_tickets(tickets) if t.meta.status == status)


def explain_idle(tickets: Sequence[Ticket]) -> IdleReason | None:
    """Why ``next_ready`` is None, or None if a ticket is ready to run.

    The first that applies wins: ``all_done``, ``running``, ``awaiting_approval``,
    ``blocked``, ``waiting`` (ready tickets whose dependencies are not done) and
    ``plan_not_approved`` (only drafts are left). Raises PlanError if the plan is
    invalid.
    """
    if next_ready(tickets) is not None:
        return None
    if all(ticket.meta.status == "done" for ticket in tickets):
        return IdleReason("all_done", (), "all tickets are done")
    if running := _ids(tickets, "running"):
        verb = "is" if len(running) == 1 else "are"
        return IdleReason("running", running, f"{', '.join(running)} {verb} running")
    if awaiting := _ids(tickets, "awaiting_approval"):
        return IdleReason(
            "awaiting_approval", awaiting, f"waiting for approval of {', '.join(awaiting)}"
        )
    if blocked := _ids(tickets, "blocked"):
        verb = "is" if len(blocked) == 1 else "are"
        return IdleReason("blocked", blocked, f"{', '.join(blocked)} {verb} blocked")
    if ready := _ids(tickets, "ready"):
        statuses = _statuses(tickets)
        waits = {
            ticket.id: tuple(_unmet(ticket, statuses))
            for ticket in sort_tickets(tickets)
            if ticket.meta.status == "ready"
        }
        parts = [f"{tid} waits for {', '.join(deps)}" for tid, deps in waits.items()]
        return IdleReason("waiting", ready, "; ".join(parts), waits)
    drafts = _ids(tickets, "draft")
    return IdleReason(
        "plan_not_approved",
        drafts,
        f"the plan is not approved yet: {', '.join(drafts)} still in draft",
    )
