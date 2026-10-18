"""The ticket frontmatter model.

Fields are strict (no ``"1"`` -> ``1`` coercion) and unknown keys are errors, so a typo
never silently falls back to a default. Only single files are checked here; unknown
dependencies and cycles are checks on the whole plan.
"""

import re
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

TicketStatus = Literal["draft", "ready", "running", "awaiting_approval", "blocked", "done"]
TICKET_STATUSES: tuple[str, ...] = get_args(TicketStatus)

TICKET_ID_RE = re.compile(r"T\d{2,3}")
TICKET_ID_RULE = "must be T followed by 2 or 3 digits, like T04"
MAX_ESTIMATE_H = 40

# Set as validation context by the store, so `id` must match the file-name prefix.
FILE_ID_CONTEXT = "file_id"


def check_ticket_id(value: str) -> str:
    if not TICKET_ID_RE.fullmatch(value):
        raise ValueError(TICKET_ID_RULE)
    return value


class TicketMeta(BaseModel):
    """The YAML frontmatter at the top of a ticket file."""

    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)

    id: str
    title: str
    phase: int = Field(ge=0)
    depends_on: list[str] = Field(default_factory=list)
    status: TicketStatus
    estimate_h: float = Field(gt=0, le=MAX_ESTIMATE_H, allow_inf_nan=False)
    review_required: bool = False
    tracker_ref: str | None = None

    @field_validator("id")
    @classmethod
    def _id_matches_file(cls, value: str, info: ValidationInfo) -> str:
        check_ticket_id(value)
        file_id = (info.context or {}).get(FILE_ID_CONTEXT)
        if file_id is not None and value != file_id:
            raise ValueError(f"{value!r} does not match the file name prefix {file_id!r}")
        return value

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value

    @field_validator("status", mode="before")
    @classmethod
    def _known_status(cls, value: object) -> object:
        # Runs before the Literal check so the message lists the statuses plainly.
        if not isinstance(value, str) or value not in TICKET_STATUSES:
            raise ValueError(f"must be one of {', '.join(TICKET_STATUSES)}")
        return value

    @field_validator("depends_on")
    @classmethod
    def _deps_are_ids(cls, value: list[str], info: ValidationInfo) -> list[str]:
        problems = []
        seen: set[str] = set()
        for dep in value:
            if not TICKET_ID_RE.fullmatch(dep):
                problems.append(f"{dep!r} is not a ticket id ({TICKET_ID_RULE})")
            elif dep == info.data.get("id"):
                problems.append(f"{dep} cannot depend on itself")
            elif dep in seen:
                problems.append(f"{dep} is listed more than once")
            seen.add(dep)
        if problems:
            raise ValueError("; ".join(dict.fromkeys(problems)))
        return value


class DoneItem(BaseModel):
    """One checklist item under a ticket's ``## Done when`` heading."""

    model_config = ConfigDict(frozen=True)

    text: str
    checked: bool
