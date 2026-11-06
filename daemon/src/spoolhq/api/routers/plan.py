"""Plan endpoints: the plan's state and problems, generate a project's plan from its
spec and approve it (token required). Thin: the work is ``services.runloop.PlanJobs``'s,
which runs the planner on the daemon's worker and records it in the run log as a run of
kind ``plan``.
"""

from fastapi import APIRouter, Request, Security, status

from spoolhq.api.errors import service_errors
from spoolhq.api.params import ProjectName
from spoolhq.api.schemas.plan import GeneratePlan, PlanApproved, PlanStarted, PlanView
from spoolhq.api.schemas.runs import RunView
from spoolhq.api.security import bearer_scheme
from spoolhq.services.runloop import PlanJobs

router = APIRouter(prefix="/api/projects/{name}/plan", dependencies=[Security(bearer_scheme)])


def _plans(request: Request) -> PlanJobs:
    plans: PlanJobs = request.app.state.plans
    return plans


@router.get("")
def get_plan(name: ProjectName, request: Request) -> PlanView:
    with service_errors():
        return PlanView.of(_plans(request).overview(name))


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
def generate_plan(
    name: ProjectName, request: Request, body: GeneratePlan | None = None
) -> PlanStarted:
    with service_errors():
        run = _plans(request).start(name, body.template_description if body else None)
    return PlanStarted(run_id=run.id, run=RunView.of(run))


@router.post("/approve")
def approve_plan(name: ProjectName, request: Request) -> PlanApproved:
    with service_errors():
        return PlanApproved(approved=list(_plans(request).approve(name)))
