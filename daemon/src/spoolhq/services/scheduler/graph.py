"""Checks on the plan as a whole: unknown dependencies, cycles and duplicate ids."""

from collections import defaultdict
from collections.abc import Iterable, Sequence

from spoolhq.services.scheduler.errors import PlanError, PlanProblem
from spoolhq.services.tickets import Ticket

ARROW = " → "


def id_key(ticket_id: str) -> tuple[int, str]:
    """Sort key for ticket ids: by number, so ``T99`` comes before ``T100``."""
    return int(ticket_id[1:]), ticket_id


def sort_ids(ids: Iterable[str]) -> list[str]:
    return sorted(ids, key=id_key)


def sort_tickets(tickets: Iterable[Ticket]) -> list[Ticket]:
    return sorted(tickets, key=lambda ticket: id_key(ticket.id))


def _and_list(items: Sequence[str]) -> str:
    """``a and b``, ``a, b and c``: two items or more."""
    return f"{', '.join(items[:-1])} and {items[-1]}"


def validate_plan(tickets: Sequence[Ticket]) -> list[PlanProblem]:
    """Every problem with the plan at once; an empty list means the plan is valid.

    Reports dependencies on ids that do not exist, each distinct cycle (members in
    order, starting from the lowest id) and ids defined in more than one file.
    """
    files: dict[str, list[str]] = defaultdict(list)
    deps: dict[str, set[str]] = defaultdict(set)
    for ticket in tickets:
        files[ticket.id].append(ticket.file_name)
        deps[ticket.id].update(ticket.meta.depends_on)

    problems: list[PlanProblem] = []
    for ticket_id in sort_ids(deps):
        for dep in sort_ids(deps[ticket_id] - files.keys()):
            problems.append(
                PlanProblem(
                    "unknown_dependency",
                    (ticket_id, dep),
                    f"{ticket_id} depends on {dep}, which does not exist",
                )
            )
    for cycle in _find_cycles(deps):
        problems.append(
            PlanProblem("cycle", tuple(cycle), "cycle: " + ARROW.join([*cycle, cycle[0]]))
        )
    for ticket_id in sort_ids(files):
        names = sorted(files[ticket_id])
        if len(names) > 1:
            problems.append(
                PlanProblem(
                    "duplicate_id",
                    (ticket_id,),
                    f"{ticket_id} is defined in {_and_list(names)}",
                )
            )
    return problems


def require_valid(tickets: Sequence[Ticket]) -> None:
    """Raise PlanError listing every problem if the plan is invalid."""
    problems = validate_plan(tickets)
    if problems:
        raise PlanError(problems)


def _find_cycles(deps: dict[str, set[str]]) -> list[list[str]]:
    """The cycles a depth-first walk in id order finds, each reported once.

    Walks from each ticket to the tickets that depend on it, so a cycle reads in work
    order (``T07 → T08`` means T08 depends on T07), like the critical path. Every back
    edge gives one cycle, rotated to start at its lowest id; this covers every group of
    tickets that depend on each other without listing every possible loop.
    """
    dependents: dict[str, list[str]] = defaultdict(list)
    for ticket_id, ticket_deps in deps.items():
        for dep in ticket_deps:
            if dep in deps:
                dependents[dep].append(ticket_id)
    for ticket_id in dependents:
        dependents[ticket_id] = sort_ids(dependents[ticket_id])

    cycles: dict[tuple[str, ...], None] = {}
    finished: set[str] = set()
    for root in sort_ids(deps):
        if root in finished:
            continue
        path: list[str] = [root]
        on_path = {root: 0}
        stack = [iter(dependents[root])]
        while stack:
            node = next(stack[-1], None)
            if node is None:
                stack.pop()
                done = path.pop()
                del on_path[done]
                finished.add(done)
            elif node in on_path:
                members = path[on_path[node] :]
                start = members.index(min(members, key=id_key))
                cycles[tuple(members[start:] + members[:start])] = None
            elif node not in finished:
                on_path[node] = len(path)
                path.append(node)
                stack.append(iter(dependents[node]))
    return sorted((list(cycle) for cycle in cycles), key=lambda c: [id_key(i) for i in c])
