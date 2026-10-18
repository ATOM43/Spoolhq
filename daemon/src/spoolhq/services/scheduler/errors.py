"""Scheduler errors: an invalid plan, or a status change the table does not allow."""

from dataclasses import dataclass
from typing import Literal

ProblemCode = Literal["unknown_dependency", "cycle", "duplicate_id"]


@dataclass(frozen=True)
class PlanProblem:
    """One problem with the plan as a whole, with the ticket ids it is about."""

    code: ProblemCode
    ticket_ids: tuple[str, ...]
    message: str


class SchedulerError(Exception):
    """Base class for scheduler errors; the message is meant for the user."""


class PlanError(SchedulerError):
    """The plan is invalid; ``problems`` lists every problem ``validate_plan`` found."""

    def __init__(self, problems: list[PlanProblem]) -> None:
        lines = "\n".join(f"  {problem.message}" for problem in problems)
        super().__init__(f"the plan has problems:\n{lines}")
        self.problems = problems


class TransitionError(SchedulerError):
    """A ticket cannot move to the requested status; the message says why."""
