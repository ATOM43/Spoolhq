"""Ticket endpoints: list, read and edit tickets (ETag + If-Match), and unblock one with
a note (token required). Edits go through the ticket store, so unchanged keys keep their
bytes, and status changes through the scheduler's transition table."""

from typing import Annotated

from fastapi import APIRouter, Query, Request, Response, Security

from spoolhq.api.errors import ApiError, service_errors
from spoolhq.api.params import (
    IfMatch,
    ProjectName,
    TicketId,
    require_if_match,
    run_log,
    settings,
    workspace,
)
from spoolhq.api.schemas.runs import RunView
from spoolhq.api.schemas.tickets import (
    InvalidTicketView,
    Note,
    TicketList,
    TicketUpdate,
    TicketView,
)
from spoolhq.api.security import bearer_scheme
from spoolhq.services.projects import EditConflict, read_with_etag, write_if_match
from spoolhq.services.runloop import RunLoop
from spoolhq.services.runs import ticket_activity
from spoolhq.services.scheduler import edit_ticket
from spoolhq.services.tickets import (
    TicketStatus,
    find_ticket_file,
    list_tickets,
    parse_ticket,
)

router = APIRouter(prefix="/api/projects/{name}/tickets", dependencies=[Security(bearer_scheme)])


@router.get("")
def get_tickets(
    name: ProjectName,
    request: Request,
    status: Annotated[TicketStatus | None, Query()] = None,
    phase: Annotated[int | None, Query(ge=0)] = None,
) -> TicketList:
    workspace(request, name)
    with service_errors():
        listing = list_tickets(
            name, projects_dir=settings(request).projects_dir, status=status, phase=phase
        )
    activity = ticket_activity(run_log(request, name))
    return TicketList(
        tickets=[TicketView.of(ticket, activity.get(ticket.id)) for ticket in listing.tickets],
        invalid=[InvalidTicketView.of(invalid) for invalid in listing.invalid],
    )


def _read(name: str, ticket_id: str, request: Request) -> tuple[TicketView, str]:
    """The ticket and the ETag of the very bytes it was parsed from."""
    with service_errors():
        path = find_ticket_file(name, ticket_id, projects_dir=settings(request).projects_dir)
        data, etag = read_with_etag(path)
        return TicketView.of(parse_ticket(data.decode("utf-8"), path.name)), etag


@router.get("/{ticket_id}")
def get_ticket(
    name: ProjectName, ticket_id: TicketId, request: Request, response: Response
) -> TicketView:
    workspace(request, name)
    view, response.headers["ETag"] = _read(name, ticket_id, request)
    return view


@router.put("/{ticket_id}")
def put_ticket(
    name: ProjectName,
    ticket_id: TicketId,
    body: TicketUpdate,
    request: Request,
    response: Response,
    if_match: IfMatch = None,
) -> TicketView:
    folder = workspace(request, name)
    expected = require_if_match(if_match)
    projects_dir = settings(request).projects_dir
    with service_errors():
        path = find_ticket_file(name, ticket_id, projects_dir=projects_dir)
        try:
            response.headers["ETag"] = write_if_match(
                folder,
                path,
                expected,
                lambda: edit_ticket(
                    name, ticket_id, body.meta, body.body, projects_dir=projects_dir
                ),
            )
        except EditConflict as exc:
            current = TicketView.of(parse_ticket(exc.data.decode("utf-8"), path.name))
            raise ApiError(
                412, "edit_conflict", str(exc), etag=exc.etag, current=current.model_dump()
            ) from exc
    return _read(name, ticket_id, request)[0]


@router.post("/{ticket_id}/unblock")
def unblock_ticket(name: ProjectName, ticket_id: TicketId, body: Note, request: Request) -> RunView:
    """Continue a blocked ticket's run with your note: a new attempt whose prompt has it."""
    loop: RunLoop = request.app.state.runloop
    with service_errors():
        return RunView.of(loop.unblock(name, ticket_id, body.note))
