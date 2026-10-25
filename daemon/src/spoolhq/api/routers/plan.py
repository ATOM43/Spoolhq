"""Plan endpoints: generate a project's plan from its spec and approve it (token
required). Thin: the work is ``services.runloop.PlanJobs``'s, which runs the planner on
the daemon's worker and records it in the run log as a run of kind ``plan``.
"""

from fastapi import APIRouter, HTTPException, Request, Security, status

from spoolhq.api.schemas.plan import GeneratePlan, PlanApproved, PlanStarted
from spoolhq.api.schemas.runs import RunView
from spoolhq.api.security import bearer_scheme
from spoolhq.services.runloop import NotFoundError, PlanJobs, RunLoopError

router = APIRouter(prefix="/api/projects/{name}", dependencies=[Security(bearer_scheme)])


def _plans(request: Request) -> PlanJobs:
    plans: PlanJobs = request.app.state.plans
    return plans


@router.post("/plan", status_code=status.HTTP_202_ACCEPTED)
def generate_plan(name: str, request: Request, body: GeneratePlan | None = None) -> PlanStarted:
    try:
        run = _plans(request).start(name, body.template_description if body else None)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except RunLoopError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return PlanStarted(run_id=run.id, run=RunView.of(run))


@router.post("/plan/approve")
def approve_plan(name: str, request: Request) -> PlanApproved:
    try:
        return PlanApproved(approved=list(_plans(request).approve(name)))
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except RunLoopError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
