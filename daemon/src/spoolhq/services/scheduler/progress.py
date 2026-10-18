"""Progress figures: hours left, the critical path and a per-status summary."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import cast

from spoolhq.core.ids import id_key
from spoolhq.services.scheduler.graph import require_valid, sort_tickets
from spoolhq.services.tickets import TICKET_STATUSES, Ticket, TicketStatus


@dataclass(frozen=True)
class CriticalPath:
    ticket_ids: tuple[str, ...]
    """In work order: each ticket depends on the one before it."""
    hours: float


@dataclass(frozen=True)
class PlanSummary:
    counts: Mapping[TicketStatus, int]
    """Every status, in the order of ``TICKET_STATUSES``, including zero counts."""
    remaining_hours: float
    critical_path: CriticalPath


def _hours(ticket: Ticket) -> Decimal:
    # Summed as decimals, so 0.1 + 0.2 equals 0.3 and ties are exact.
    return Decimal(str(ticket.meta.estimate_h))


def remaining_hours(tickets: Sequence[Ticket]) -> float:
    """The sum of ``estimate_h`` over tickets that are not done.

    Raises PlanError if the plan is invalid.
    """
    require_valid(tickets)
    return float(sum((_hours(t) for t in tickets if t.meta.status != "done"), Decimal(0)))


def critical_path(tickets: Sequence[Ticket]) -> CriticalPath:
    """The longest chain of not-done tickets by summed ``estimate_h``.

    Each ticket in the chain depends on the one before it. Of chains with the same
    hours, the one whose ids are lowest (compared ticket by ticket from the start) wins,
    so the result is deterministic. Raises PlanError if the plan is invalid.
    """
    require_valid(tickets)
    open_tickets = {t.id: t for t in sort_tickets(tickets) if t.meta.status != "done"}
    dependents: dict[str, list[str]] = {tid: [] for tid in open_tickets}
    for ticket in open_tickets.values():
        for dep in ticket.meta.depends_on:
            if dep in open_tickets:
                dependents[dep].append(ticket.id)

    # The best chain starting at each ticket, filled in after all its dependents.
    best: dict[str, tuple[Decimal, tuple[str, ...]]] = {}
    for tid in reversed(_work_order(open_tickets, dependents)):
        tail_hours, tail = max(
            (best[d] for d in dependents[tid]),
            key=_rank,
            default=(Decimal(0), ()),
        )
        best[tid] = (_hours(open_tickets[tid]) + tail_hours, (tid, *tail))
    hours, chain = max(best.values(), key=_rank, default=(Decimal(0), ()))
    return CriticalPath(chain, float(hours))


def _rank(chain: tuple[Decimal, tuple[str, ...]]) -> tuple[Decimal, list[int]]:
    """Ranks longer chains higher, then chains with lower ids (negated, for ``max``).

    Estimates are above 0, so of two chains with the same hours neither is a prefix of
    the other and the first differing id decides.
    """
    hours, ids = chain
    return hours, [-id_key(tid)[0] for tid in ids]


def _work_order(tickets: Mapping[str, Ticket], dependents: Mapping[str, list[str]]) -> list[str]:
    """The ids in an order where every ticket comes after its dependencies (Kahn)."""
    waiting = {tid: sum(dep in tickets for dep in t.meta.depends_on) for tid, t in tickets.items()}
    queue = [tid for tid, count in waiting.items() if count == 0]
    order: list[str] = []
    while queue:
        tid = queue.pop()
        order.append(tid)
        for dependent in dependents[tid]:
            waiting[dependent] -= 1
            if waiting[dependent] == 0:
                queue.append(dependent)
    return order


def summary(tickets: Sequence[Ticket]) -> PlanSummary:
    """Counts per status, remaining hours and the critical path.

    Raises PlanError if the plan is invalid.
    """
    require_valid(tickets)
    counts = dict.fromkeys(cast(tuple[TicketStatus, ...], TICKET_STATUSES), 0)
    for ticket in tickets:
        counts[ticket.meta.status] += 1
    return PlanSummary(
        counts=counts,
        remaining_hours=remaining_hours(tickets),
        critical_path=critical_path(tickets),
    )
