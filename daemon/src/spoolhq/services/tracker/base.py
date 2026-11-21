"""The interface every tracker adapter implements, and what all of them share.

The sync service (``sync.py``) and the run loop use only this interface; an adapter is
picked by ``tracker.kind`` in ``registry.py``. Adapters raise ``TrackerError`` with a
fixed message (never a token, header or response body).
"""

from typing import Protocol

from spoolhq.services.tickets import Ticket

FOOTER = "Synced by SpoolHQ · edit in SpoolHQ, not here"


class TrackerError(Exception):
    """A call to the tracker failed. ``retry_after`` (seconds) is set when the tracker
    asked to wait (a rate limit); such a wait isn't counted as a failure."""

    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class TrackerAdapter(Protocol):
    def push_ticket(self, ticket: Ticket) -> str:
        """Update the ticket's task when ``ticket.meta.tracker_ref`` is set; otherwise
        adopt the task whose name starts with ``task_prefix(ticket.id)`` or create one.
        Sends the name, the description and the mapped status; returns the task's ref."""
        ...

    def update_status(self, ref: str, status: str) -> None:
        """Set the task's status to the one ``status`` (a ticket status) maps to."""
        ...

    def comment(self, ref: str, text: str) -> None: ...

    def link_pr(self, ref: str, url: str) -> None: ...

    def close(self) -> None: ...


def task_prefix(ticket_id: str) -> str:
    """How every task name starts; finding a task by it is the crash recovery."""
    return f"{ticket_id} · "


def task_name(ticket: Ticket) -> str:
    return task_prefix(ticket.id) + ticket.meta.title


def description(ticket: Ticket) -> str:
    """The ticket's body (scope and "Done when", markdown) and the SpoolHQ footer."""
    return f"{ticket.body.strip()}\n\n---\n{FOOTER}\n"
