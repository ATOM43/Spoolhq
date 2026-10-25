"""GitHub endpoints: check a project's open pull requests now (token required). Thin:
the work is ``services.runloop.GitHubPoller``'s, which also runs every 60 s."""

from fastapi import APIRouter, Request, Security

from spoolhq.api.routers.runs import errors
from spoolhq.api.schemas.github import GitHubSync
from spoolhq.api.security import bearer_scheme
from spoolhq.services.runloop import GitHubPoller

router = APIRouter(prefix="/api/projects/{name}/github", dependencies=[Security(bearer_scheme)])


@router.post("/sync")
def sync(name: str, request: Request) -> GitHubSync:
    poller: GitHubPoller = request.app.state.github
    with errors():
        return GitHubSync(lines=poller.sync(name))
