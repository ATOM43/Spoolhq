"""Reading and checking the planner's ``<plan>`` block: pure and deterministic.

The last ``<plan>`` block in the final message is parsed as JSON and validated with
Pydantic; then the ids are checked against the tickets that already exist, each ticket
is rendered as a draft file and parsed back through the tickets store, and the combined
graph (kept tickets plus the new plan) goes through the scheduler's plan validation.
"""

import json
import re
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from spoolhq.core.ids import TICKET_ID_RE, id_key
from spoolhq.services.planner.model import InvalidPlan, PlanOutput
from spoolhq.services.planner.store import Existing, draft_file_name, render_draft
from spoolhq.services.scheduler import validate_plan
from spoolhq.services.tickets import Ticket, TicketValidationError, parse_ticket

_BLOCK_RE = re.compile(r"<plan>(.*?)</plan>", re.DOTALL | re.IGNORECASE)
_FENCE_RE = re.compile(r"\A```[A-Za-z]*\n(.*)\n```\Z", re.DOTALL)


def next_id(existing: Existing) -> str:
    """The first id after every ticket that exists now (``T01`` for an empty project)."""
    ids = [ticket.id for ticket in (*existing.kept, *existing.replaceable)]
    number = max((id_key(ticket_id)[0] for ticket_id in ids), default=0) + 1
    return f"T{number:02d}"


def _where(loc: tuple[int | str, ...], raw: Any) -> str:
    """``T05: estimate_h`` for an error inside a ticket that has a readable id."""
    parts = [str(part) for part in loc]
    if len(loc) >= 2 and loc[0] == "tickets" and isinstance(loc[1], int):
        try:
            ticket_id = raw["tickets"][loc[1]]["id"]
        except (KeyError, IndexError, TypeError):
            ticket_id = None
        if isinstance(ticket_id, str) and TICKET_ID_RE.fullmatch(ticket_id):
            return ": ".join([ticket_id, ".".join(parts[2:])]) if loc[2:] else ticket_id
    return ".".join(parts) or "plan"


def parse_plan(final_text: str) -> PlanOutput:
    """The last ``<plan>`` block in ``final_text``; raises InvalidPlan listing every problem."""
    blocks = _BLOCK_RE.findall(final_text)
    if not blocks:
        raise InvalidPlan(["no <plan> block in the final message"])
    text = blocks[-1].strip()
    fence = _FENCE_RE.match(text)
    if fence:
        text = fence[1].strip()
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidPlan([f"the <plan> block is not valid JSON: {exc}"]) from None
    try:
        # From the JSON text: strict mode accepts JSON arrays as tuples only there.
        return PlanOutput.model_validate_json(text)
    except ValidationError as exc:
        raise InvalidPlan(
            [f"{_where(err['loc'], raw)}: {err['msg']}" for err in exc.errors()]
        ) from None


@dataclass(frozen=True)
class CheckedPlan:
    drafts: dict[str, str]
    """File name → text of each draft file, in id order."""
    tickets: tuple[Ticket, ...]
    """The drafts as parsed by the tickets store, in id order."""


def _id_errors(output: PlanOutput, existing: Existing) -> list[str]:
    kept = {ticket.id for ticket in existing.kept}
    reusable = {ticket.id for ticket in existing.replaceable}
    first = next_id(existing)
    errors: list[str] = []
    seen: set[str] = set()
    for planned in output.tickets:
        ticket_id = planned.id
        if ticket_id in seen:
            errors.append(f"{ticket_id}: the id appears more than once")
        elif ticket_id in kept:
            errors.append(f"{ticket_id}: the id belongs to a kept ticket")
        elif ticket_id not in reusable and id_key(ticket_id) < id_key(first):
            errors.append(f"{ticket_id}: new ids continue from {first}")
        seen.add(ticket_id)
    return errors


def check_plan(output: PlanOutput, existing: Existing, test_command: str) -> CheckedPlan:
    """Check ``output`` against the tickets that exist; raises InvalidPlan listing every
    problem. New ids may reuse the ids of the drafts being replaced; any other id must
    come after the highest existing one."""
    errors = _id_errors(output, existing)
    drafts: dict[str, str] = {}
    tickets: list[Ticket] = []
    for planned in sorted(output.tickets, key=lambda planned: id_key(planned.id)):
        name, text = draft_file_name(planned), render_draft(planned, test_command)
        try:
            tickets.append(parse_ticket(text, name))
        except TicketValidationError as exc:
            errors.extend(exc.errors)
            continue
        drafts[name] = text
    if errors:
        raise InvalidPlan(errors)

    new_ids = {ticket.id for ticket in tickets}
    dropped = {ticket.id for ticket in existing.replaceable} - new_ids
    reported: set[tuple[str, ...]] = set()
    for ticket in existing.kept:
        for dep in ticket.meta.depends_on:
            if dep in dropped:
                errors.append(f"{ticket.id} is kept and depends on {dep}, which the new plan drops")
                reported.add((ticket.id, dep))
    for problem in validate_plan([*existing.kept, *tickets]):
        if problem.ticket_ids not in reported:
            errors.append(problem.message)
    if errors:
        raise InvalidPlan(errors)
    return CheckedPlan(drafts, tuple(tickets))
