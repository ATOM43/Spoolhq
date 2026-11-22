"""Tracker endpoints: a project's sync state, queuing a push of every ticket, and retrying
what failed. Thin: the work is ``services.tracker.TrackerSync``'s, whose thread sends the
queued actions."""

from dataclasses import asdict

from fastapi import APIRouter, Request, Security

from spoolhq.api.errors import service_errors
from spoolhq.api.params import ProjectName
from spoolhq.api.schemas.tracker import TrackerPush, TrackerView
from spoolhq.api.security import bearer_scheme
from spoolhq.services.tracker.sync import TrackerSync

router = APIRouter(prefix="/api/projects/{name}/tracker", dependencies=[Security(bearer_scheme)])


@router.get("")
def get_tracker(name: ProjectName, request: Request) -> TrackerView:
    sync: TrackerSync = request.app.state.tracker
    with service_errors():
        return TrackerView(**asdict(sync.status(name)))


@router.post("/push")
def push(name: ProjectName, request: Request) -> TrackerPush:
    sync: TrackerSync = request.app.state.tracker
    with service_errors():
        return TrackerPush(queued=sync.push_all(name))


@router.post("/retry")
def retry(name: ProjectName, request: Request) -> TrackerPush:
    """Re-queue the failed actions; 200 with ``queued: 0`` when none failed."""
    sync: TrackerSync = request.app.state.tracker
    with service_errors():
        return TrackerPush(queued=sync.retry(name))
