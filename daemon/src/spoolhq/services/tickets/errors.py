"""Ticket errors, in the ``project.yaml`` style: ``tickets/<file>: <field>: <message>``."""

TICKETS_DIR = "tickets"


class TicketError(Exception):
    """A ticket could not be found, read or saved; the message says why."""


class TicketValidationError(TicketError):
    """A ticket file is invalid; ``errors`` lists every problem, one line each."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


def source_name(file_name: str) -> str:
    """``T04-x.md`` -> ``tickets/T04-x.md``, the prefix of every message about the file."""
    return f"{TICKETS_DIR}/{file_name}"
