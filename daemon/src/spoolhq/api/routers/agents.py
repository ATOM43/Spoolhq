"""``GET /api/agents``: the agent backends on this machine and Graphify, as
``spool agents`` shows them (token required), and the dev fake runner's scenario when it
is active. Detection never starts an agent."""

from fastapi import APIRouter, Request, Security

from spoolhq.api.schemas.agents import AgentsView, BackendView, GraphifyView
from spoolhq.api.security import bearer_scheme
from spoolhq.services.agents import available_runners
from spoolhq.services.codegraph import probe

router = APIRouter(prefix="/api", dependencies=[Security(bearer_scheme)])


@router.get("/agents")
def agents(request: Request) -> AgentsView:
    return AgentsView(
        backends=[BackendView.of(runner.detect()) for runner in available_runners()],
        graphify=GraphifyView.of(probe()),
        fake_runner=request.app.state.fake_runner,
    )
