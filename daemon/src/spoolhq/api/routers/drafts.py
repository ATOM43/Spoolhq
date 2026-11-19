"""Draft endpoints: draft tickets from a few lines with the planner, read or cancel the
job, and save the edited drafts together (token required). Thin: the work is
``services.runloop.DraftJobs``' and ``services.scheduler.create_tickets``'."""

from fastapi import APIRouter, Request, Security, status

from spoolhq.api.errors import ApiError, service_errors
from spoolhq.api.params import ProjectName, settings, workspace
from spoolhq.api.routers.jobs import JobId
from spoolhq.api.schemas.drafts import (
    DraftJobView,
    DraftRequest,
    DraftStarted,
    TicketBatch,
    TicketsSaved,
)
from spoolhq.api.schemas.tickets import TicketView
from spoolhq.api.security import bearer_scheme
from spoolhq.services.runloop import DraftJobs, NotFoundError
from spoolhq.services.scheduler import create_tickets

router = APIRouter(prefix="/api/projects/{name}/tickets", dependencies=[Security(bearer_scheme)])


def _drafts(request: Request) -> DraftJobs:
    drafts: DraftJobs = request.app.state.drafts
    return drafts


@router.post("/draft", status_code=status.HTTP_202_ACCEPTED)
def start_draft(name: ProjectName, body: DraftRequest, request: Request) -> DraftStarted:
    """Start drafting 1 to 3 tickets; 409 with the reason when the planner's agent isn't
    ready (`agent_unavailable`), a run is going or a plan is being generated."""
    with service_errors():
        return DraftStarted(job_id=_drafts(request).start(name, body.request).id)


@router.get("/draft/{job_id}")
def get_draft(name: ProjectName, job_id: JobId, request: Request) -> DraftJobView:
    """The draft job; its drafts and their problems once it succeeded (kept 1 hour)."""
    try:
        return DraftJobView.of(_drafts(request).get(name, job_id))
    except NotFoundError as exc:
        raise ApiError(404, "not_found", str(exc)) from exc


@router.post("/draft/{job_id}/cancel")
def cancel_draft(name: ProjectName, job_id: JobId, request: Request) -> DraftJobView:
    """Stop the agent; answers once the job ended (at most 15 s)."""
    try:
        return DraftJobView.of(_drafts(request).cancel(name, job_id))
    except NotFoundError as exc:
        raise ApiError(404, "not_found", str(exc)) from exc


@router.post("/batch", status_code=status.HTTP_201_CREATED)
def save_batch(name: ProjectName, body: TicketBatch, request: Request) -> TicketsSaved:
    """Save edited drafts: ids in draft order, refs rewritten, all files or none."""
    workspace(request, name)
    with service_errors():
        tickets = create_tickets(name, body.tickets, projects_dir=settings(request).projects_dir)
    return TicketsSaved(tickets=[TicketView.of(ticket) for ticket in tickets])
