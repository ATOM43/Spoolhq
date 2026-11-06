"""Request and response models of the ticket endpoints."""

from dataclasses import asdict

from pydantic import BaseModel, Field

from spoolhq.services.runs import TicketActivity
from spoolhq.services.tickets import InvalidTicket, Ticket, TicketMeta


class TicketActivityView(BaseModel):
    attempts: int
    tokens: int
    """Tokens of attempts without a cost (subscription backends)."""
    cost_micro_usd: int | None
    """Summed cost of attempts with one (API-key backends); null if none."""
    run_id: int | None
    """The ticket's latest run."""
    reason: str | None
    """That run's reason: why it is blocked or waits for approval."""

    @classmethod
    def of(cls, activity: TicketActivity) -> "TicketActivityView":
        return cls(**asdict(activity))


class TicketView(BaseModel):
    id: str
    file_name: str
    meta: TicketMeta
    """The frontmatter."""
    body: str
    """Everything after the frontmatter, exactly as stored."""
    activity: TicketActivityView | None = None
    """In the list only: the ticket's runs so far; null before its first run."""

    @classmethod
    def of(cls, ticket: Ticket, activity: TicketActivity | None = None) -> "TicketView":
        return cls(
            id=ticket.id,
            file_name=ticket.file_name,
            meta=ticket.meta,
            body=ticket.body,
            activity=TicketActivityView.of(activity) if activity else None,
        )


class InvalidTicketView(BaseModel):
    file_name: str
    errors: list[str]

    @classmethod
    def of(cls, invalid: InvalidTicket) -> "InvalidTicketView":
        return cls(file_name=invalid.file_name, errors=invalid.errors)


class TicketList(BaseModel):
    tickets: list[TicketView]
    invalid: list[InvalidTicketView]
    """Files that don't load, whatever the filters."""


class TicketUpdate(BaseModel):
    meta: TicketMeta
    body: str = Field(max_length=900_000)


class Note(BaseModel):
    note: str = Field(default="", max_length=100_000)
    """What the agent should do; required (an empty note is refused with 409)."""
