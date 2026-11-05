"""Creation jobs: read one while it runs, cancel it, or dismiss one that ended (token
required). Thin: the work is ``services.creation.CreationJobs``'s; ``POST /api/projects``
starts a job."""

from typing import Annotated

from fastapi import APIRouter, Path, Request, Security, status

from spoolhq.api.errors import ApiError
from spoolhq.api.schemas.jobs import JobView
from spoolhq.api.security import bearer_scheme
from spoolhq.services.creation import CreationJobs, UnknownJobError

router = APIRouter(prefix="/api/jobs", dependencies=[Security(bearer_scheme)])
JobId = Annotated[str, Path(pattern=r"^[0-9a-f]{32}$", description="Job id.")]


def _jobs(request: Request) -> CreationJobs:
    jobs: CreationJobs = request.app.state.creation
    return jobs


@router.get("/{job_id}")
def get_job(job_id: JobId, request: Request) -> JobView:
    try:
        return JobView.of(_jobs(request).get(job_id))
    except UnknownJobError as exc:
        raise ApiError(404, "not_found", "no such job") from exc


@router.post("/{job_id}/cancel")
def cancel_job(job_id: JobId, request: Request) -> JobView:
    """Stop the job and roll back; answers once the rollback is done (at most 15 s)."""
    try:
        return JobView.of(_jobs(request).cancel(job_id))
    except UnknownJobError as exc:
        raise ApiError(404, "not_found", "no such job") from exc


@router.post("/{job_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_job(job_id: JobId, request: Request) -> None:
    """Forget an ended job, so the project list stops showing what it left behind."""
    try:
        _jobs(request).dismiss(job_id)
    except UnknownJobError as exc:
        raise ApiError(404, "not_found", "no such job") from exc
