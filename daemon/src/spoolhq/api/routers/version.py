"""``GET /api/version``: the daemon's version (token required)."""

from fastapi import APIRouter, Security

import spoolhq
from spoolhq.api.schemas.version import Version
from spoolhq.api.security import bearer_scheme

router = APIRouter(prefix="/api", dependencies=[Security(bearer_scheme)])


@router.get("/version")
def version() -> Version:
    return Version(version=spoolhq.__version__)
