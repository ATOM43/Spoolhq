"""The plan as the Tickets tab reviews it: its state, its size and every problem that
stops it from being approved."""

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Literal

from spoolhq.services.planner.store import PLAN_FILE, plan_problems
from spoolhq.services.projects import project_dir
from spoolhq.services.scheduler import PlanProblem
from spoolhq.services.tickets import list_tickets

PlanState = Literal["none", "planning", "draft", "approved"]


@dataclass(frozen=True)
class PlanOverview:
    state: PlanState
    generated_at: str | None
    """When the planner last wrote the plan (``plan.json``); None if it never did."""
    ticket_count: int
    """The drafts while the plan is a draft (what approving moves), else every ticket."""
    total_h: float
    problems: tuple[PlanProblem, ...]


def _generated_at(workspace: Path) -> str | None:
    try:
        value = json.loads((workspace / PLAN_FILE).read_text(encoding="utf-8"))["generated_at"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return value if isinstance(value, str) else None


def plan_overview(project: str, *, projects_dir: Path, planning: bool = False) -> PlanOverview:
    """The project's plan; raises TicketError for an unknown project."""
    listing = list_tickets(project, projects_dir=projects_dir)
    drafts = [ticket for ticket in listing.tickets if ticket.meta.status == "draft"]
    state: PlanState = (
        "planning" if planning else "draft" if drafts else "approved" if listing.tickets else "none"
    )
    counted = drafts or listing.tickets
    hours = sum((Decimal(str(ticket.meta.estimate_h)) for ticket in counted), Decimal(0))
    return PlanOverview(
        state=state,
        generated_at=_generated_at(project_dir(project, projects_dir)),
        ticket_count=len(counted),
        total_h=float(hours),
        problems=tuple(plan_problems(listing.tickets, listing.invalid)),
    )
