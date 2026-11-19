"""``POST /api/repos/inspect``: what an existing repo already has (token required).
Thin: the work is ``services.creation.inspect_repo``'s; it reads files and never runs a
command."""

from dataclasses import asdict

from fastapi import APIRouter, Request, Security

from spoolhq.api.errors import ApiError
from spoolhq.api.params import settings
from spoolhq.api.schemas.repos import InspectRepo, RepoInspectionView
from spoolhq.api.security import bearer_scheme
from spoolhq.core.config import home_dir
from spoolhq.services.creation import CreationError, inspect_repo

router = APIRouter(prefix="/api/repos", dependencies=[Security(bearer_scheme)])


@router.post("/inspect")
def inspect(body: InspectRepo, request: Request) -> RepoInspectionView:
    """422 with field ``path`` for a path a creation would refuse; a dirty repo is
    reported, not refused."""
    config = settings(request)
    own = [config.projects_dir, config.worktrees_dir, home_dir()]
    try:
        found = inspect_repo(body.path, own_folders=own)
    except CreationError as exc:
        raise ApiError(422, "validation_error", exc.message, field="path") from exc
    return RepoInspectionView.model_validate(asdict(found))
