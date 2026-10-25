"""The plan the planner agent returns, and what ``generate_plan`` reports.

The agent's ``<plan>`` JSON is untrusted: it is validated with strict Pydantic models
(unknown keys refused), and every text field is cleaned to one line without control
characters before it reaches a ticket file.
"""

import unicodedata
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field, field_validator

from spoolhq.core.ids import TICKET_ID_RE, TICKET_ID_RULE
from spoolhq.services.agents import Outcome

MIN_ESTIMATE_H = 1.5
MAX_ESTIMATE_H = 4
TITLE_MAX = 80


class PlannerError(Exception):
    """The plan can't be generated, written or approved; the message says why."""


class InvalidPlan(PlannerError):
    """The planner's output can't be used; ``errors`` says why, one line each."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


def one_line(text: str) -> str:
    """``text`` on one line: whitespace runs become one space, control characters go."""
    kept = (
        " " if char.isspace() else char
        for char in text
        if char.isspace() or unicodedata.category(char) not in ("Cc", "Cf")
    )
    return " ".join("".join(kept).split())


def clean_title(text: str) -> str:
    """One line of at most ``TITLE_MAX`` characters."""
    return one_line(text)[:TITLE_MAX].rstrip()


def _not_blank(value: str) -> str:
    if not value:
        raise ValueError("must not be empty")
    return value


class PlannedTicket(BaseModel):
    """One ticket in the planner's ``<plan>`` block."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    id: str
    title: str
    phase: int = Field(ge=0)
    purpose: str
    depends_on: tuple[str, ...] = ()
    estimate_h: float = Field(ge=MIN_ESTIMATE_H, le=MAX_ESTIMATE_H, allow_inf_nan=False)
    review_required: bool = False
    scope: tuple[str, ...] = Field(min_length=1)
    done_when: tuple[str, ...] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def _id(cls, value: str) -> str:
        if not TICKET_ID_RE.fullmatch(value):
            raise ValueError(TICKET_ID_RULE)
        return value

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        return _not_blank(clean_title(value))

    @field_validator("purpose")
    @classmethod
    def _purpose(cls, value: str) -> str:
        return _not_blank(one_line(value))

    @field_validator("scope", "done_when")
    @classmethod
    def _items(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        items = tuple(one_line(item) for item in value)
        if not all(items):
            raise ValueError("items must not be empty")
        return items


class PlanOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    tickets: tuple[PlannedTicket, ...] = Field(min_length=1)


@dataclass(frozen=True)
class PlanResult:
    """What one ``generate_plan`` call did; ``error`` is None when the plan was written."""

    outcome: Outcome
    error: str | None
    written: tuple[str, ...]
    """Ids of the draft files written, in id order."""
    deleted: tuple[str, ...]
    """Ids of the unedited drafts the new plan dropped."""
    kept: tuple[str, ...]
    """Ids of the tickets kept as they were (not drafts, edited or hand-made drafts)."""
    attempts: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cost_micro_usd: int | None
