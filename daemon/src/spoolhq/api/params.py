"""Path parameters checked by pattern before any route code runs, so a name or id can
never become a path outside the projects folder."""

from pathlib import Path as PathLike
from typing import Annotated

from fastapi import Header, Path, Request

from spoolhq.api.errors import ApiError
from spoolhq.core.config import Settings
from spoolhq.services.projects import project_dir
from spoolhq.services.runs import RunLog, RunRegistry

ProjectName = Annotated[
    str, Path(pattern=r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$", description="Project name.")
]
TicketId = Annotated[str, Path(pattern=r"^T\d{2,3}$", description="Ticket id, like T04.")]
IfMatch = Annotated[str | None, Header(description="The ETag from the last GET.")]


def settings(request: Request) -> Settings:
    value: Settings = request.app.state.settings
    return value


def workspace(request: Request, name: str) -> PathLike:
    """The project's folder; 404 unless it is a workspace (it has a ``project.yaml``)."""
    folder = project_dir(name, settings(request).projects_dir)
    if not (folder / "project.yaml").is_file():
        raise ApiError(404, "not_found", f"no project {name!r}")
    return folder


def run_log(request: Request, name: str) -> RunLog:
    registry: RunRegistry = request.app.state.runs
    return registry.open(workspace(request, name)).run_log


def require_if_match(if_match: str | None) -> str:
    if if_match is None:
        raise ApiError(
            428, "precondition_required", "send If-Match with the ETag from your last GET"
        )
    return if_match
