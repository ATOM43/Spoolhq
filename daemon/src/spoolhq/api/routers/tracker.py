"""Tracker endpoints: a project's sync state, and queuing a push of every ticket. Thin:
the work is ``services.tracker.TrackerSync``'s, whose thread sends the queued actions."""

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
