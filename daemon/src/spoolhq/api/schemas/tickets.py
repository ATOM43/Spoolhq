"""Request and response models of the ticket endpoints."""

from pydantic import BaseModel, Field

from spoolhq.services.tickets import InvalidTicket, Ticket, TicketMeta


class TicketView(BaseModel):
    id: str
    file_name: str
    meta: TicketMeta
    """The frontmatter."""
    body: str
    """Everything after the frontmatter, exactly as stored."""

    @classmethod
    def of(cls, ticket: Ticket) -> "TicketView":
        return cls(id=ticket.id, file_name=ticket.file_name, meta=ticket.meta, body=ticket.body)


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
