"""Planner: from a project's spec to draft tickets the user reviews and approves.

``generate_plan()`` runs a read-only agent (Read, Glob, Grep) in the project's
repository with ``CONTEXT.md``, an optional template description and the tickets that
must be kept; its ``<plan>`` block is validated in code and written as ``draft`` ticket
files. ``approve_plan()`` moves every draft to ``ready``; nothing runs before that.
``plan_overview()`` is the plan's state, size and problems for the Tickets tab.
This package may import ``services.agents``, ``services.context``,
``services.projects``, ``services.scheduler`` and ``services.tickets``. See
``docs/planner.md``.
"""

from spoolhq.services.planner.model import (
    MAX_ESTIMATE_H,
    MIN_ESTIMATE_H,
    TITLE_MAX,
    InvalidPlan,
    PlanInvalid,
    PlannedTicket,
    PlannerError,
    PlanOutput,
    PlanResult,
    clean_title,
    one_line,
)
from spoolhq.services.planner.overview import PlanOverview, PlanState, plan_overview
from spoolhq.services.planner.planner import PLANNER_MAX_TURNS, generate_plan, read_spec
from spoolhq.services.planner.prompt import PLANNER_TEMPLATE, render_planner_prompt
from spoolhq.services.planner.store import (
    PLAN_FILE,
    Existing,
    approve_plan,
    load_existing,
    plan_problems,
    render_draft,
    write_plan,
)
from spoolhq.services.planner.validate import CheckedPlan, check_plan, next_id, parse_plan

__all__ = [
    "MAX_ESTIMATE_H",
    "MIN_ESTIMATE_H",
    "PLANNER_MAX_TURNS",
    "PLANNER_TEMPLATE",
    "PLAN_FILE",
    "TITLE_MAX",
    "CheckedPlan",
    "Existing",
    "InvalidPlan",
    "PlanInvalid",
    "PlanOutput",
    "PlanOverview",
    "PlanState",
    "PlanResult",
    "PlannedTicket",
    "PlannerError",
    "approve_plan",
    "check_plan",
    "clean_title",
    "generate_plan",
    "load_existing",
    "next_id",
    "one_line",
    "parse_plan",
    "plan_overview",
    "plan_problems",
    "read_spec",
    "render_draft",
    "render_planner_prompt",
    "write_plan",
]
